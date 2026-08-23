"""
main.py
--------
FastAPI application entrypoint.

Run with:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import init_db
from api.routes import router, UPLOAD_DIR

app = FastAPI(
    title="Knee OA & Implant Sizing Prototype API",
    description=(
        "Hackathon research/decision-support prototype for (1) medial "
        "meniscus thickness assessment vs osteoarthritis, age and sex, "
        "and (2) patient-specific femoral/tibial measurement for knee "
        "implant sizing. NOT a diagnostic device and does not replace "
        "clinical judgement."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Knee OA & Implant Sizing Prototype API",
        "disclaimer": "Clinical decision-support/research prototype only. "
                      "Does not provide autonomous diagnosis.",
    }