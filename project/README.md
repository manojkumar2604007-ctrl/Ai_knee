# AI-Assisted Medial Meniscus Thickness Assessment & Patient-Specific Knee Implant Sizing

Hackathon prototype implementing exactly two modules described in the problem statement:

1. **Medial meniscus + OA analysis** — segment femur/tibia/medial meniscus, measure
   meniscus thickness at anterior/mid/posterior locations, compare OA vs Non-OA and
   Male vs Female populations.
2. **Patient-specific femoral/tibial measurement for implant sizing** — segment
   femur/tibia, extract width + AP dimensions, match against a configurable implant
   database, return ranked size candidates.

This is a **clinical decision-support / research prototype**. It does **not** diagnose
osteoarthritis, does **not** replace a clinician, and does **not** use any real trained
medical imaging model or real implant manufacturer specs (see "Demo vs Real Model" below).

---

## Project Structure

```
project/
├── backend/
│   ├── main.py                       # FastAPI app entrypoint
│   ├── database.py                   # SQLite connection + init + placeholder implant seed
│   ├── knee_prototype.db             # created automatically on first run
│   ├── models/
│   │   └── schemas.py                # Pydantic request/response models
│   ├── services/
│   │   ├── image_utils.py            # preprocessing + calibration (mm/pixel) reading
│   │   ├── segmentation.py           # AI segmentation interface (mock + real-model hook)
│   │   ├── meniscus_measurement.py   # meniscus thickness measurement (separate from AI code)
│   │   ├── bone_measurement.py       # femur/tibia width & AP measurement
│   │   ├── oa_analysis.py            # OA vs Non-OA, Male vs Female statistics
│   │   └── implant_matching.py       # ranked implant size matching
│   ├── api/
│   │   └── routes.py                 # all REST endpoints
│   ├── uploads/                      # uploaded images stored here
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/               # PatientForm, ImageUpload, ImageViewer,
│   │   │                             # MeniscusResults, OAComparison, BoneMeasurements,
│   │   │                             # ImplantMatching, FinalReport
│   │   ├── pages/
│   │   │   └── Dashboard.js          # composes all components into the dashboard
│   │   ├── services/
│   │   │   └── api.js                # fetch wrappers for the backend API
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   ├── public/index.html
│   └── package.json
│
├── database/
│   └── schema.sql                    # patients, images, measurements, implants tables
│
└── README.md
```

---

## Installation & Running

### 1. Backend (Python / FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The SQLite database and its tables are created automatically on startup
(`database.py:init_db()` runs `database/schema.sql` and seeds a few
**placeholder** implant sizing rows). No manual DB setup step is required,
but you can also run the schema manually if you prefer:

```bash
sqlite3 backend/knee_prototype.db < database/schema.sql
```

Start the API:

```bash
uvicorn main:app --reload --port 8000
```

API docs (Swagger UI) will be available at: `http://localhost:8000/docs`

### 2. Frontend (React)

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000` and talks to the backend at `http://localhost:8000`
(configurable via `REACT_APP_API_BASE` env var, see `frontend/src/services/api.js`).

---

## API Reference & Usage Examples

| Method | Path | Purpose |
|---|---|---|
| POST | `/patient` | Create a patient (age, sex, oa_status) |
| GET | `/patient/{id}` | Get patient + their images + measurements |
| POST | `/upload?patient_id=1` | Upload a knee image (multipart form file) |
| POST | `/analyze` | Run the full analysis pipeline |
| GET | `/measurements/{id}` | Get stored measurements for a patient |
| GET | `/implant-recommendation/{id}` | Get ranked implant size matches |
| GET | `/oa-comparison` | Population-wide OA/sex statistical comparison |
| POST | `/implant-database` | Add a validated implant sizing row |
| GET | `/implant-database` | List all implant sizing rows |

### Example: full flow with curl

```bash
# 1. Create a patient
curl -X POST http://localhost:8000/patient \
  -H "Content-Type: application/json" \
  -d '{"name":"Sample","age":58,"sex":"F","oa_status":"OA"}'
# -> {"id":1, ...}

# 2. Upload an image
curl -X POST "http://localhost:8000/upload?patient_id=1" \
  -F "file=@sample_data/sample_knee.png"
# -> {"image_id":1,"pixel_spacing_mm":null,"message":"Physical measurement unavailable ..."}

# 3. Analyze (supplying manual calibration since the sample PNG has no DICOM spacing metadata)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"patient_id":1,"image_id":1,"manual_mm_per_pixel":0.25}'

# 4. Get implant recommendation
curl http://localhost:8000/implant-recommendation/1

# 5. Get OA vs Non-OA / Male vs Female comparison across all analyzed patients
curl http://localhost:8000/oa-comparison

# 6. Add a validated implant size (replace placeholder data)
curl -X POST http://localhost:8000/implant-database \
  -H "Content-Type: application/json" \
  -d '{"implant_system":"YourValidatedSystem","component_type":"femoral","size":"M","femoral_width":66.5,"femoral_ap":61.0}'
```

### Sample test data

`sample_data/generate_sample_image.py` (see below) creates a synthetic grayscale
PNG you can use to exercise the pipeline without a real medical image. For real
testing, use any anonymized knee X-ray/MRI PNG/JPG, or a DICOM file (`.dcm`) —
DICOM files let the system read real physical pixel spacing automatically.

Create it with:
```bash
mkdir -p sample_data
python3 - <<'EOF'
import numpy as np, cv2
img = np.random.randint(40, 200, (400, 300), dtype=np.uint8)
cv2.imwrite("sample_data/sample_knee.png", img)
EOF
```

---

## Calibration Rule (Important)

The system **never** silently assumes a pixel-to-millimetre conversion:

1. On `/upload`, it attempts to read physical pixel spacing from DICOM metadata
   (`SimpleITK` `GetSpacing()`).
2. If unavailable, `/analyze` accepts a `manual_mm_per_pixel` calibration value.
3. If neither is available, all measurement endpoints return
   `"Physical measurement unavailable — image calibration required."` and
   **never** present pixel counts as millimetres.

---

## Demo/Mock Mode vs Real Trained Model

**No trained medical segmentation model or annotated dataset was provided** with
this problem statement, so `backend/services/segmentation.py` ships with:

- `KneeSegmentationModel` — an abstract PyTorch `nn.Module` interface any real
  trained model must implement (`predict(image) -> {femur_mask, tibia_mask,
  medial_meniscus_mask}`).
- `MockKneeSegmentationModel` — the **default**, active model. It produces
  placeholder masks using simple thresholding + fixed anatomical-region
  heuristics (upper half ≈ femur, lower half ≈ tibia, a thin medial band ≈
  meniscus). **This is not a real medical AI prediction** — every API response
  and dashboard panel labels its output with `"mode": "demo_mock"` and a visible
  disclaimer.

### To connect a real trained model

1. Train (or obtain) a segmentation model (e.g. U-Net / nnU-Net) on annotated
   knee MRI/X-ray data with femur/tibia/medial-meniscus labels.
2. Implement a subclass of `KneeSegmentationModel` in `segmentation.py` that
   loads your weights and implements `predict()` to return real masks.
3. In `get_segmentation_model()`, set `MODE = "trained_model"` and return an
   instance of your subclass.
4. No other file needs to change — the measurement, OA-analysis, and implant
   matching services only depend on the `segment_knee()` output contract.

The system will then report `"mode": "trained_model"` everywhere instead of
`"demo_mock"`, and the frontend disclaimer updates automatically.

---

## Implant Database

The `implants` table (see `database/schema.sql`) is seeded with a handful of
**placeholder** rows (`implant_system = "PLACEHOLDER-System"`) purely so the
matching pipeline can be demonstrated end-to-end. These are **not** real
manufacturer specifications. Replace them with validated dimensions via:

```
POST /implant-database
{
  "implant_system": "...",
  "component_type": "femoral" | "tibial",
  "size": "...",
  "femoral_width": ..., "femoral_ap": ...,   // for femoral components
  "tibial_width": ..., "tibial_ap": ...      // for tibial components
}
```

---

## Optional Add-on Module: Sex / Skeletal Maturity Estimate

An **optional, separable** add-on was added on top of the two required
modules: `GET /demographic-estimate/{patient_id}`, backed by
`backend/services/demographic_estimation.py` and shown as its own panel
(`frontend/src/components/DemographicEstimate.js`) below the final report.

- Uses a simple **threshold heuristic** on femoral bicondylar width
  (`FEMORAL_WIDTH_SEX_THRESHOLD_MM` in `demographic_estimation.py`) to
  give a coarse, illustrative "statistically skews Male/Female/Uncertain"
  read-out. The threshold is a **placeholder** — replace it with a
  validated, population-appropriate value from published literature
  before relying on this for anything beyond a demo.
- Never outputs a numeric age. Skeletal maturity is reported only as
  "Not assessable in this prototype," since real maturity assessment
  requires growth-plate detection this prototype does not implement.
- Every response carries an explicit disclaimer and is clearly labelled
  as an experimental statistical estimate requiring clinician review.
- **Fully separable**: it does not feed into the OA/meniscus comparison
  or implant-sizing logic. The age/sex entered in the patient form
  remains the authoritative source for those calculations. Deleting
  `demographic_estimation.py`, its API route, and its frontend component
  removes this add-on with no effect on the two core modules.

## Restrictions Honored

- No chatbot, general diagnosis, medicine recommendation, hospital management,
  appointment booking, patient monitoring, or unrelated X-ray disease detection.
- No autonomous diagnosis claim anywhere in API responses or UI — every implant
  and OA-related output is labelled "for clinician review" / "research prototype".
- No invented OA clinical thresholds — `oa_analysis.py` only performs descriptive
  statistics (mean, std dev, Welch's t-test) on user-supplied OA labels.
- No invented real implant manufacturer specs — implant database ships empty of
  real data, only clearly-labelled placeholders, and is configurable via API.
- Pixel-to-mm conversion is never silent — see "Calibration Rule" above.