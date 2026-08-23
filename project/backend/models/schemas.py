"""
schemas.py
----------
Pydantic request/response models shared across the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class PatientCreate(BaseModel):
    name: Optional[str] = None
    age: int = Field(..., ge=0, le=120)
    sex: Literal["M", "F", "Other"]
    oa_status: Literal["OA", "Non-OA", "Unknown"]


class PatientOut(PatientCreate):
    id: int
    created_at: str


class AnalyzeRequest(BaseModel):
    patient_id: int
    image_id: int
    # Manual calibration fallback, in millimetres per pixel.
    # Required only if the uploaded image has no physical spacing metadata.
    manual_mm_per_pixel: Optional[float] = None


class ImplantCreate(BaseModel):
    implant_system: str
    component_type: Literal["femoral", "tibial"]
    size: str
    femoral_width: Optional[float] = None
    femoral_ap: Optional[float] = None
    tibial_width: Optional[float] = None
    tibial_ap: Optional[float] = None
    notes: Optional[str] = None


class ImplantMatch(BaseModel):
    size: str
    implant_system: str
    match_score: float


class ImplantRecommendationOut(BaseModel):
    calibration_status: str
    femoral_recommendations: List[ImplantMatch]
    tibial_recommendations: List[ImplantMatch]
    disclaimer: str = "AI-assisted sizing suggestions for clinician review."