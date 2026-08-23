"""
image_utils.py
---------------
Preprocessing + physical-spacing (calibration) utilities.

Per the problem statement, the system must NEVER silently assume a
pixel-to-millimetre conversion. This module tries, in order:
  1. Read physical pixel spacing from image metadata (DICOM via
     SimpleITK, if the file is a DICOM series/file).
  2. Fall back to a manual calibration value supplied by the caller
     (e.g. via the /analyze request body).
  3. If neither is available, return mm_per_pixel=None and callers
     must display: "Physical measurement unavailable — image
     calibration required."
"""

import os
from typing import Optional, Tuple
import numpy as np
import cv2

try:
    import SimpleITK as sitk
    _SITK_AVAILABLE = True
except ImportError:
    _SITK_AVAILABLE = False

DICOM_EXTENSIONS = {".dcm", ".dicom"}


def load_image_grayscale(file_path: str) -> np.ndarray:
    """
    Loads an image as a single-channel (grayscale) numpy array.
    Supports standard image formats (PNG/JPG) via OpenCV and DICOM via
    SimpleITK when available.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in DICOM_EXTENSIONS and _SITK_AVAILABLE:
        sitk_image = sitk.ReadImage(file_path)
        array = sitk.GetArrayFromImage(sitk_image)  # (slices, H, W) or (H, W)
        if array.ndim == 3:
            array = array[0]  # take first slice for a single 2D image
        array = cv2.normalize(array, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return array

    image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"Could not read image file: {file_path}")
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def read_pixel_spacing_mm(file_path: str) -> Tuple[Optional[float], str]:
    """
    Attempts to read physical pixel spacing (mm/pixel) from image
    metadata.

    Returns:
        (mm_per_pixel or None, source) where source is one of:
        "metadata" | "unavailable"
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext in DICOM_EXTENSIONS and _SITK_AVAILABLE:
        try:
            sitk_image = sitk.ReadImage(file_path)
            spacing = sitk_image.GetSpacing()  # (x, y[, z]) in mm
            if spacing and len(spacing) >= 2:
                # Use the average of x/y in-plane spacing as a single
                # scalar mm-per-pixel value for 2D measurements.
                mm_per_pixel = (spacing[0] + spacing[1]) / 2.0
                if mm_per_pixel and mm_per_pixel > 0:
                    return mm_per_pixel, "metadata"
        except Exception:
            pass

    return None, "unavailable"


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Basic preprocessing shared by both analysis modules:
    denoising + contrast normalization. Kept simple/transparent for a
    hackathon prototype.
    """
    denoised = cv2.fastNlMeansDenoising(image, h=7)
    normalized = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return normalized