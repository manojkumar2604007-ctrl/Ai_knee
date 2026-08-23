"""
implant_matching.py
---------------------
Compares patient-specific femoral/tibial measurements against a
configurable implant sizing database and returns ranked candidate
sizes with a match score.

The implant database (see database/schema.sql -> `implants` table) is
seeded only with clearly-labelled PLACEHOLDER dimensions
(database.py:_seed_placeholder_implants). Real validated manufacturer
implant dimensions must be inserted via POST /implant-database before
this module's output should be used for anything beyond a demo.

Match score definition:
    score = 1 / (1 + normalized_euclidean_distance)
    where normalized_euclidean_distance is computed over the relevant
    dimension pair (width, AP) scaled by each dimension's typical range
    in the candidate set, so score is in (0, 1], 1.0 = perfect match.
    This is a simple, transparent nearest-neighbour heuristic - NOT a
    clinically validated sizing algorithm.
"""

from typing import Dict, List, Optional
import math


def _normalized_distance(patient_dims, candidate_dims, ranges) -> float:
    total = 0.0
    count = 0
    for key in patient_dims:
        p = patient_dims[key]
        c = candidate_dims.get(key)
        if p is None or c is None:
            continue
        r = ranges.get(key) or 1.0
        total += ((p - c) / r) ** 2
        count += 1
    if count == 0:
        return float("inf")
    return math.sqrt(total / count)


def _compute_ranges(candidates: List[Dict], keys: List[str]) -> Dict[str, float]:
    ranges = {}
    for key in keys:
        values = [c[key] for c in candidates if c.get(key) is not None]
        if values:
            span = max(values) - min(values)
            ranges[key] = span if span > 0 else max(values) or 1.0
        else:
            ranges[key] = 1.0
    return ranges


def match_implant_size(
    patient_width_mm: Optional[float],
    patient_ap_mm: Optional[float],
    candidates: List[Dict],
    component_type: str,
    top_n: int = 3,
) -> List[Dict]:
    """
    Args:
        patient_width_mm / patient_ap_mm: patient measurements (mm). If
            either is None (uncalibrated image), matching cannot be
            performed and an empty list is returned.
        candidates: rows from the `implants` table filtered to
            component_type, each a dict with keys like
            femoral_width/femoral_ap or tibial_width/tibial_ap, size,
            implant_system.
        component_type: "femoral" | "tibial"
        top_n: number of ranked matches to return.

    Returns:
        List of {"size", "implant_system", "match_score"} sorted best-first.
    """
    if patient_width_mm is None or patient_ap_mm is None:
        return []

    if component_type == "femoral":
        width_key, ap_key = "femoral_width", "femoral_ap"
    else:
        width_key, ap_key = "tibial_width", "tibial_ap"

    valid_candidates = [c for c in candidates if c.get(width_key) is not None and c.get(ap_key) is not None]
    if not valid_candidates:
        return []

    ranges = _compute_ranges(valid_candidates, [width_key, ap_key])
    patient_dims = {width_key: patient_width_mm, ap_key: patient_ap_mm}

    scored = []
    for c in valid_candidates:
        candidate_dims = {width_key: c[width_key], ap_key: c[ap_key]}
        dist = _normalized_distance(patient_dims, candidate_dims, ranges)
        score = 1.0 / (1.0 + dist) if dist != float("inf") else 0.0
        scored.append({
            "size": c["size"],
            "implant_system": c["implant_system"],
            "match_score": round(score, 4),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_n]