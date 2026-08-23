-- ============================================================
-- Knee OA + Implant Sizing Prototype - Database Schema
-- SQLite prototype schema. Replace/extend with a production
-- database (e.g. PostgreSQL) for real deployments.
-- ============================================================

-- Patient demographic + clinical info
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL CHECK (sex IN ('M', 'F', 'Other')),
    oa_status TEXT NOT NULL CHECK (oa_status IN ('OA', 'Non-OA', 'Unknown')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Uploaded images (DICOM / PNG / JPG) linked to a patient
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT,
    pixel_spacing_mm REAL,          -- physical spacing read from metadata (mm/pixel), NULL if unknown
    calibration_source TEXT,        -- 'metadata' | 'manual' | 'unavailable'
    uploaded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- Segmentation + measurement results (one row per analysis run)
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    image_id INTEGER NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('demo_mock', 'trained_model')),

    -- Meniscus thickness at predefined anatomical locations (mm, or NULL if uncalibrated)
    meniscus_anterior_mm REAL,
    meniscus_mid_mm REAL,
    meniscus_posterior_mm REAL,
    meniscus_mean_mm REAL,

    -- Femoral measurements (mm)
    femoral_width_mm REAL,
    femoral_ap_mm REAL,

    -- Tibial measurements (mm)
    tibial_width_mm REAL,
    tibial_ap_mm REAL,

    calibration_status TEXT,  -- 'calibrated' | 'uncalibrated'
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (image_id) REFERENCES images(id)
);

-- Configurable implant sizing database (populate with validated
-- manufacturer dimensions later -- values here are placeholders only)
CREATE TABLE IF NOT EXISTS implants (
    implant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    implant_system TEXT NOT NULL,      -- e.g. "System-A" (placeholder, not a real product)
    component_type TEXT NOT NULL CHECK (component_type IN ('femoral', 'tibial')),
    size TEXT NOT NULL,                -- e.g. "S", "M", "L" or numeric size code
    femoral_width REAL,
    femoral_ap REAL,
    tibial_width REAL,
    tibial_ap REAL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_images_patient ON images(patient_id);
CREATE INDEX IF NOT EXISTS idx_measurements_patient ON measurements(patient_id);
CREATE INDEX IF NOT EXISTS idx_implants_component ON implants(component_type);