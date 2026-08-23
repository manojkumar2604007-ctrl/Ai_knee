"""
meniscus_measurement.py
------------------------
Measures medial meniscus thickness at predefined anatomical locations
(anterior, mid, posterior) from a segmentation mask.

Measurement logic is kept STRICTLY separate from the AI segmentation
code (see services/segmentation.py). This module only consumes mask
arrays - it never touches model weights or inference code.

CALIBRATION RULE (per problem statement):
    Pixel-to-millimetre conversion is NEVER assumed silently.
    Callers must supply `mm_per_pixel`. If it is None, this module
    returns pixel-only measurements and a calibration_status of
    "uncalibrated" - callers (API layer) must then surface:
    "Physical measurement unavailable - image calibration required."
"""

from typing import Dict, Optional, List
import numpy as np

# Predefined sampling locations along the joint-space band, expressed
# as fractions of the meniscus mask's horizontal extent.
ANATOMICAL_LOCATIONS = {
    "anterior": 0.2,
    "mid": 0.5,
    "posterior": 0.8,
}


def _column_thickness_px(mask: np.ndarray, col: int) -> Optional[int]:
    """Count contiguous mask pixels (thickness in px) in a given column."""
    if col < 0 or col >= mask.shape[1]:
        return None
    column = mask[:, col]
    thickness = int(np.sum(column > 0))
    return thickness if thickness > 0 else None


def measure_meniscus_thickness(
    medial_meniscus_mask: np.ndarray,
    mm_per_pixel: Optional[float] = None,
) -> Dict:
    """
    Measures meniscus thickness at anterior / mid / posterior locations.

    Args:
        medial_meniscus_mask: binary mask (H x W), 1 = meniscus pixel.
        mm_per_pixel: physical spacing. None => cannot compute mm values.

    Returns:
        {
            "calibration_status": "calibrated" | "uncalibrated",
            "locations_px": {"anterior": int|None, "mid": ..., "posterior": ...},
            "locations_mm": {"anterior": float|None, ...} (None if uncalibrated),
            "mean_mm": float|None,
            "message": str|None  # populated only when uncalibrated
        }
    """
    cols_with_mask = np.where(medial_meniscus_mask.sum(axis=0) > 0)[0]
    if len(cols_with_mask) == 0:
        locations_px = {loc: None for loc in ANATOMICAL_LOCATIONS}
    else:
        min_col, max_col = cols_with_mask.min(), cols_with_mask.max()
        span = max_col - min_col
        locations_px = {}
        for loc_name, frac in ANATOMICAL_LOCATIONS.items():
            col = int(min_col + frac * span)
            locations_px[loc_name] = _column_thickness_px(medial_meniscus_mask, col)

    result = {
        "calibration_status": "calibrated" if mm_per_pixel else "uncalibrated",
        "locations_px": locations_px,
        "locations_mm": None,
        "mean_mm": None,
        "message": None,
    }

    if not mm_per_pixel:
        result["message"] = "Physical measurement unavailable — image calibration required."
        return result

    locations_mm = {
        loc: (round(px * mm_per_pixel, 3) if px is not None else None)
        for loc, px in locations_px.items()
    }
    valid_values = [v for v in locations_mm.values() if v is not None]
    mean_mm = round(sum(valid_values) / len(valid_values), 3) if valid_values else None

    result["locations_mm"] = locations_mm
    result["mean_mm"] = mean_mm
    return result