"""
routes.py
----------
All FastAPI route definitions for the prototype.
"""

import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from database import get_connection
from models.schemas import (
    PatientCreate, AnalyzeRequest, ImplantCreate,
)
from services import image_utils, segmentation
from services.meniscus_measurement import measure_meniscus_thickness
from services.bone_measurement import measure_femur_dimensions, measure_tibia_dimensions
from services.oa_analysis import compare_oa_groups
from services.implant_matching import match_implant_size
from services.demographic_estimation import get_demographic_estimate

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------------------------------------
# Patient management (needed to support /analyze, /patient/{id}, etc.)
# ------------------------------------------------------------------

@router.post("/patient")
def create_patient(patient: PatientCreate):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO patients (name, age, sex, oa_status) VALUES (?, ?, ?, ?)",
            (patient.name, patient.age, patient.sex, patient.oa_status),
        )
        conn.commit()
        patient_id = cur.lastrowid
        row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        return row


@router.get("/patient/{patient_id}")
def get_patient(patient_id: int):
    with get_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        measurements = conn.execute(
            "SELECT * FROM measurements WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()
        images = conn.execute(
            "SELECT * FROM images WHERE patient_id = ? ORDER BY uploaded_at DESC",
            (patient_id,),
        ).fetchall()
        return {"patient": patient, "images": images, "measurements": measurements}


# ------------------------------------------------------------------
# Image upload
# ------------------------------------------------------------------

@router.post("/upload")
async def upload_image(patient_id: int, file: UploadFile = File(...)):
    with get_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

    ext = os.path.splitext(file.filename)[1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(stored_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    mm_per_pixel, source = image_utils.read_pixel_spacing_mm(stored_path)

    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO images (patient_id, file_path, file_type, pixel_spacing_mm, calibration_source)
               VALUES (?, ?, ?, ?, ?)""",
            (patient_id, stored_path, ext, mm_per_pixel, source),
        )
        conn.commit()
        image_id = cur.lastrowid

    return {
        "image_id": image_id,
        "patient_id": patient_id,
        "calibration_source": source,
        "pixel_spacing_mm": mm_per_pixel,
        "message": None if mm_per_pixel else
            "Physical measurement unavailable — image calibration required. "
            "Supply manual_mm_per_pixel in /analyze if you want physical (mm) measurements.",
    }


# ------------------------------------------------------------------
# Analysis pipeline
# ------------------------------------------------------------------

@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    with get_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id = ?", (request.patient_id,)).fetchone()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        image_row = conn.execute(
            "SELECT * FROM images WHERE id = ? AND patient_id = ?",
            (request.image_id, request.patient_id),
        ).fetchone()
        if not image_row:
            raise HTTPException(status_code=404, detail="Image not found for this patient")

    # Determine mm/pixel: metadata first, then manual override.
    mm_per_pixel = image_row["pixel_spacing_mm"] or request.manual_mm_per_pixel
    calibration_status = "calibrated" if mm_per_pixel else "uncalibrated"

    # --- Pipeline: preprocessing -> segmentation -> measurement -> matching ---
    raw_image = image_utils.load_image_grayscale(image_row["file_path"])
    processed_image = image_utils.preprocess_image(raw_image)

    masks = segmentation.segment_knee(processed_image)

    meniscus_result = measure_meniscus_thickness(masks["medial_meniscus_mask"], mm_per_pixel)
    femur_result = measure_femur_dimensions(masks["femur_mask"], mm_per_pixel)
    tibia_result = measure_tibia_dimensions(masks["tibia_mask"], mm_per_pixel)

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO measurements (
                patient_id, image_id, mode,
                meniscus_anterior_mm, meniscus_mid_mm, meniscus_posterior_mm, meniscus_mean_mm,
                femoral_width_mm, femoral_ap_mm,
                tibial_width_mm, tibial_ap_mm,
                calibration_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.patient_id, request.image_id, masks["mode"],
                (meniscus_result["locations_mm"] or {}).get("anterior"),
                (meniscus_result["locations_mm"] or {}).get("mid"),
                (meniscus_result["locations_mm"] or {}).get("posterior"),
                meniscus_result["mean_mm"],
                femur_result["width_mm"], femur_result["ap_mm"],
                tibia_result["width_mm"], tibia_result["ap_mm"],
                calibration_status,
            ),
        )
        conn.commit()
        measurement_id = cur.lastrowid

    # Implant matching (only meaningful if calibrated)
    with get_connection() as conn:
        femoral_candidates = conn.execute(
            "SELECT * FROM implants WHERE component_type = 'femoral'"
        ).fetchall()
        tibial_candidates = conn.execute(
            "SELECT * FROM implants WHERE component_type = 'tibial'"
        ).fetchall()

    femoral_matches = match_implant_size(
        femur_result["width_mm"], femur_result["ap_mm"], femoral_candidates, "femoral"
    )
    tibial_matches = match_implant_size(
        tibia_result["width_mm"], tibia_result["ap_mm"], tibial_candidates, "tibial"
    )

    return {
        "measurement_id": measurement_id,
        "mode": masks["mode"],
        "calibration_status": calibration_status,
        "calibration_message": None if mm_per_pixel else
            "Physical measurement unavailable — image calibration required.",
        "meniscus": meniscus_result,
        "femur": femur_result,
        "tibia": tibia_result,
        "implant_recommendation": {
            "femoral_recommendations": femoral_matches,
            "tibial_recommendations": tibial_matches,
            "disclaimer": "AI-assisted sizing suggestions for clinician review.",
        },
        "segmentation_disclaimer": (
            "Demo/mock segmentation output." if masks["mode"] == "demo_mock"
            else "Trained model output — verify against clinical review."
        ),
    }


# ------------------------------------------------------------------
# Measurement + implant recommendation retrieval
# ------------------------------------------------------------------

@router.get("/measurements/{patient_id}")
def get_measurements(patient_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM measurements WHERE patient_id = ? ORDER BY created_at DESC",
            (patient_id,),
        ).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No measurements found for this patient")
        return {"patient_id": patient_id, "measurements": rows}


@router.get("/implant-recommendation/{patient_id}")
def get_implant_recommendation(patient_id: int):
    with get_connection() as conn:
        latest = conn.execute(
            "SELECT * FROM measurements WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1",
            (patient_id,),
        ).fetchone()
        if not latest:
            raise HTTPException(status_code=404, detail="No analysis found for this patient")

        femoral_candidates = conn.execute(
            "SELECT * FROM implants WHERE component_type = 'femoral'"
        ).fetchall()
        tibial_candidates = conn.execute(
            "SELECT * FROM implants WHERE component_type = 'tibial'"
        ).fetchall()

    femoral_matches = match_implant_size(
        latest["femoral_width_mm"], latest["femoral_ap_mm"], femoral_candidates, "femoral"
    )
    tibial_matches = match_implant_size(
        latest["tibial_width_mm"], latest["tibial_ap_mm"], tibial_candidates, "tibial"
    )

    return {
        "calibration_status": latest["calibration_status"],
        "femoral_recommendations": femoral_matches,
        "tibial_recommendations": tibial_matches,
        "disclaimer": "AI-assisted sizing suggestions for clinician review.",
    }


# ------------------------------------------------------------------
# OA comparative analysis (across all patients with valid measurements)
# ------------------------------------------------------------------

@router.get("/oa-comparison")
def get_oa_comparison():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT p.sex AS sex, p.oa_status AS oa_status, m.meniscus_mean_mm AS meniscus_mean_mm
            FROM measurements m
            JOIN patients p ON p.id = m.patient_id
            WHERE m.meniscus_mean_mm IS NOT NULL
            """
        ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No calibrated measurements available yet for OA comparison.",
        )
    return compare_oa_groups(rows)


# ------------------------------------------------------------------
# Implant database management (configurable per requirements)
# ------------------------------------------------------------------

@router.post("/implant-database")
def add_implant(implant: ImplantCreate):
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO implants
                (implant_system, component_type, size, femoral_width, femoral_ap,
                 tibial_width, tibial_ap, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                implant.implant_system, implant.component_type, implant.size,
                implant.femoral_width, implant.femoral_ap,
                implant.tibial_width, implant.tibial_ap, implant.notes,
            ),
        )
        conn.commit()
        implant_id = cur.lastrowid
        row = conn.execute("SELECT * FROM implants WHERE implant_id = ?", (implant_id,)).fetchone()
        return row


@router.get("/implant-database")
def list_implants():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM implants").fetchall()
        return {"implants": rows}


# ------------------------------------------------------------------
# OPTIONAL ADD-ON MODULE: demographic (sex / skeletal maturity)
# estimation. This is NOT one of the two required modules and does
# NOT feed into OA comparison or implant sizing. See
# services/demographic_estimation.py for full caveats.
# ------------------------------------------------------------------

@router.get("/demographic-estimate/{patient_id}")
def demographic_estimate(patient_id: int):
    with get_connection() as conn:
        latest = conn.execute(
            "SELECT * FROM measurements WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1",
            (patient_id,),
        ).fetchone()
        if not latest:
            raise HTTPException(status_code=404, detail="No analysis found for this patient")

    femur_result = {
        "width_mm": latest["femoral_width_mm"],
        "ap_mm": latest["femoral_ap_mm"],
    }
    tibia_result = {
        "width_mm": latest["tibial_width_mm"],
        "ap_mm": latest["tibial_ap_mm"],
    }
    return get_demographic_estimate(femur_result, tibia_result)