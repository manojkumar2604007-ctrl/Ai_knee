"""
bone_measurement.py
--------------------
Extracts femoral and tibial anatomical dimensions (width and
anteroposterior [AP] extent) from segmentation masks.

Measurement logic only - no AI/model code lives here (see
services/segmentation.py for the segmentation model interface).

CALIBRATION RULE: identical to meniscus_measurement.py - never
silently assume a pixel-to-mm conversion. `mm_per_pixel=None` yields
pixel-only output plus an explicit "uncalibrated" status.
"""

from typing import Dict, Optional
import numpy as np


def _bounding_box(mask: np.ndarray):
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return {
        "x_min": int(xs.min()), "x_max": int(xs.max()),
        "y_min": int(ys.min()), "y_max": int(ys.max()),
    }


def _measure_bone(mask: np.ndarray, mm_per_pixel: Optional[float]) -> Dict:
    """
    width  = horizontal extent of the bounding box (medio-lateral proxy)
    ap     = vertical extent of the bounding box (anteroposterior proxy)

    NOTE: In a real 2D projection image, width/AP axis assignment
    depends on imaging plane/orientation metadata. This prototype uses
    bounding-box extent as a stand-in; a production system should read
    orientation from DICOM metadata (e.g. ImageOrientationPatient) to
    correctly assign axes.
    """
    box = _bounding_box(mask)
    if box is None:
        return {
            "calibration_status": "calibrated" if mm_per_pixel else "uncalibrated",
            "width_px": None, "ap_px": None,
            "width_mm": None, "ap_mm": None,
            "message": "No bone mask pixels detected.",
        }

    width_px = box["x_max"] - box["x_min"] + 1
    ap_px = box["y_max"] - box["y_min"] + 1

    result = {
        "calibration_status": "calibrated" if mm_per_pixel else "uncalibrated",
        "width_px": width_px,
        "ap_px": ap_px,
        "width_mm": None,
        "ap_mm": None,
        "message": None,
    }

    if not mm_per_pixel:
        result["message"] = "Physical measurement unavailable — image calibration required."
        return result

    result["width_mm"] = round(width_px * mm_per_pixel, 3)
    result["ap_mm"] = round(ap_px * mm_per_pixel, 3)
    return result


def measure_femur_dimensions(femur_mask: np.ndarray, mm_per_pixel: Optional[float] = None) -> Dict:
    """Returns femoral width + AP dimension (px and mm)."""
    return _measure_bone(femur_mask, mm_per_pixel)


def measure_tibia_dimensions(tibia_mask: np.ndarray, mm_per_pixel: Optional[float] = None) -> Dict:
    """Returns tibial width + AP dimension (px and mm)."""
    return _measure_bone(tibia_mask, mm_per_pixel)