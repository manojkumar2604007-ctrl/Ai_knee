"""
oa_analysis.py
---------------
Quantitative/statistical comparison of medial meniscus thickness across:
  - OA vs Non-OA cases
  - Male vs Female populations

IMPORTANT: This module does NOT invent or embed any clinical OA
diagnostic thresholds. OA status is supplied by the user/clinician as
existing patient metadata (oa_status field) - this module only performs
descriptive statistics and a standard two-sample comparison (Welch's
t-test) on already-labelled groups. It does not diagnose OA.
"""

from typing import Dict, List
import numpy as np
from scipy import stats


def _group_stats(values: List[float]) -> Dict:
    if not values:
        return {"n": 0, "mean_mm": None, "std_mm": None}
    arr = np.array(values, dtype=float)
    return {
        "n": int(arr.size),
        "mean_mm": round(float(arr.mean()), 3),
        "std_mm": round(float(arr.std(ddof=1)), 3) if arr.size > 1 else 0.0,
    }


def _two_sample_test(group_a: List[float], group_b: List[float]) -> Dict:
    if len(group_a) < 2 or len(group_b) < 2:
        return {
            "test": "welch_ttest",
            "p_value": None,
            "note": "Insufficient sample size (need >=2 per group) for a statistical test.",
        }
    t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False, nan_policy="omit")
    return {
        "test": "welch_ttest",
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 4),
        "note": "p < 0.05 conventionally suggests a statistically significant difference "
                "between groups; this is descriptive research output, not a diagnostic threshold.",
    }


def compare_oa_groups(records: List[Dict]) -> Dict:
    """
    Args:
        records: list of dicts, each with at minimum:
            {"meniscus_mean_mm": float, "oa_status": "OA"|"Non-OA", "sex": "M"|"F"}
            Records with missing/uncalibrated meniscus_mean_mm should be
            excluded by the caller before calling this function.

    Returns a structured comparison covering OA vs Non-OA and Male vs Female.
    """
    oa_values = [r["meniscus_mean_mm"] for r in records if r.get("oa_status") == "OA"]
    non_oa_values = [r["meniscus_mean_mm"] for r in records if r.get("oa_status") == "Non-OA"]
    male_values = [r["meniscus_mean_mm"] for r in records if r.get("sex") == "M"]
    female_values = [r["meniscus_mean_mm"] for r in records if r.get("sex") == "F"]

    return {
        "sample_size_total": len(records),
        "oa_vs_non_oa": {
            "oa_group": _group_stats(oa_values),
            "non_oa_group": _group_stats(non_oa_values),
            "statistical_test": _two_sample_test(oa_values, non_oa_values),
        },
        "male_vs_female": {
            "male_group": _group_stats(male_values),
            "female_group": _group_stats(female_values),
            "statistical_test": _two_sample_test(male_values, female_values),
        },
        "disclaimer": (
            "Descriptive/statistical research output based on user-provided OA "
            "labels. This module does not diagnose osteoarthritis or apply any "
            "clinical thickness threshold."
        ),
    }