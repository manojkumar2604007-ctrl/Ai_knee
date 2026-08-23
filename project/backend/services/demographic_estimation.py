"""
demographic_estimation.py
---------------------------
OPTIONAL ADD-ON MODULE — NOT part of the original two required modules
(meniscus/OA analysis, implant sizing). This module is fully separable:
removing this file and its API route/frontend panel does not affect
Module 1 or Module 2 in any way.

PURPOSE
-------
Provides a *statistical, illustrative* estimate of:
  1. Likely biological sex, based on femoral bicondylar width.
  2. Likely skeletal maturity stage (adult vs still-growing), based on
     a simple heuristic over bone measurement completeness/shape.

IMPORTANT LIMITATIONS (read before using this for anything beyond a demo)
--------------------------------------------------------------------------
- This is NOT a trained/validated AI model. It is a simple threshold-based
  heuristic using widely-cited *population average* differences in femoral
  width between sexes. It is provided for demonstration purposes only.
- Real sex-estimation from skeletal measurements in forensic/radiology
  literature uses population- and ancestry-specific regression equations
  derived from validated reference datasets — NOT a single fixed number.
  The thresholds below are illustrative placeholders, not a substitute
  for a validated clinical/forensic method.
- This module NEVER outputs a numeric age. Adult age cannot be reliably
  estimated from a knee X-ray/MRI once growth plates have fused. It only
  reports a coarse maturity category (e.g. "likely skeletally mature").
- Every output must be clearly labelled as a statistical estimate for
  clinician review — never presented as a diagnosis or ground truth.
- Do NOT wire this into the OA/meniscus comparison or implant-sizing
  logic. It is a separate, optional, informational panel only.

HOW TO CONFIGURE THE THRESHOLD (per problem-statement pattern used
elsewhere in this project, e.g. the implant database)
--------------------------------------------------------------------------
`FEMORAL_WIDTH_SEX_THRESHOLD_MM` below is a placeholder illustrative value.
Replace it with a validated, population-appropriate value from published
literature before using this for anything beyond a hackathon demo.
"""

from typing import Dict, Optional

# PLACEHOLDER threshold only — replace with a validated, population-
# appropriate value from published literature before real use.
FEMORAL_WIDTH_SEX_THRESHOLD_MM = 68.0
FEMORAL_WIDTH_UNCERTAIN_BAND_MM = 4.0  # +/- band around threshold treated as "uncertain"


def estimate_sex_from_bone(femoral_width_mm: Optional[float]) -> Dict:
    """
    Very simple heuristic: wider femoral bicondylar width statistically
    skews male, narrower skews female, in population-average studies.
    Returns "Uncertain" whenever the measurement falls within an
    uncertainty band around the threshold, or when uncalibrated.

    This is a coarse, illustrative estimate only — never a determination.
    """
    if femoral_width_mm is None:
        return {
            "estimate": "Uncertain",
            "confidence_note": "No calibrated femoral width available.",
            "disclaimer": DISCLAIMER,
        }

    lower = FEMORAL_WIDTH_SEX_THRESHOLD_MM - FEMORAL_WIDTH_UNCERTAIN_BAND_MM
    upper = FEMORAL_WIDTH_SEX_THRESHOLD_MM + FEMORAL_WIDTH_UNCERTAIN_BAND_MM

    if lower <= femoral_width_mm <= upper:
        estimate = "Uncertain"
        note = f"Femoral width ({femoral_width_mm} mm) is within the uncertain band."
    elif femoral_width_mm > upper:
        estimate = "Statistically skews Male"
        note = f"Femoral width ({femoral_width_mm} mm) is above the illustrative threshold."
    else:
        estimate = "Statistically skews Female"
        note = f"Femoral width ({femoral_width_mm} mm) is below the illustrative threshold."

    return {
        "estimate": estimate,
        "confidence_note": note,
        "disclaimer": DISCLAIMER,
    }


def estimate_skeletal_maturity(femur_result: Dict, tibia_result: Dict) -> Dict:
    """
    Coarse heuristic only: this prototype has no growth-plate detection
    model, so it cannot truly assess skeletal maturity. It returns a
    fixed "Not assessable in this prototype" response, structured so a
    real growth-plate segmentation model could be plugged in later
    (see docstring above for the extension point).
    """
    return {
        "estimate": "Not assessable in this prototype",
        "confidence_note": (
            "Skeletal maturity (adult vs still-growing) requires detecting "
            "growth-plate (epiphyseal) fusion status, which is not "
            "implemented in this demo. A real implementation would need a "
            "trained model to detect growth plate presence/closure."
        ),
        "disclaimer": DISCLAIMER,
    }


DISCLAIMER = (
    "Experimental statistical estimate for demonstration only — NOT a "
    "validated diagnostic method. Requires clinician review. Does not "
    "determine an individual's sex or age; reflects only population-"
    "average tendencies applied to a simple bone-width measurement."
)


def get_demographic_estimate(femur_result: Dict, tibia_result: Dict) -> Dict:
    """
    Public entry point combining both estimates into one response.
    """
    sex_estimate = estimate_sex_from_bone(femur_result.get("width_mm"))
    maturity_estimate = estimate_skeletal_maturity(femur_result, tibia_result)
    return {
        "sex_estimate": sex_estimate,
        "skeletal_maturity_estimate": maturity_estimate,
        "module_note": (
            "Optional add-on module — separate from the meniscus/OA "
            "analysis and implant-sizing modules. Provided age/sex "
            "entered in the patient form remains the authoritative source "
            "for all OA/meniscus comparisons; this panel does not feed "
            "back into those calculations."
        ),
    }