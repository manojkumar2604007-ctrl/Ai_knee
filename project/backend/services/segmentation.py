"""
segmentation.py
----------------
Segmentation interface for the knee analysis pipeline.

WHY THIS FILE IS STRUCTURED THIS WAY
-------------------------------------
No trained medical segmentation model/weights were provided with this
hackathon problem statement. This file therefore defines:

  1. `KneeSegmentationModel` - an abstract PyTorch nn.Module interface
     that a REAL trained model (e.g. a U-Net trained on annotated knee
     MRI/X-ray data) must implement.

  2. `MockKneeSegmentationModel` - a clearly-labelled DEMO/MOCK
     implementation that produces PLACEHOLDER masks using simple,
     deterministic image-processing heuristics (thresholding + region
     geometry). This is NOT a real medical AI prediction. It exists
     only so the rest of the pipeline (measurement, OA comparison,
     implant matching, dashboard) can be demonstrated end-to-end.

HOW TO PLUG IN A REAL TRAINED MODEL
-------------------------------------
1. Implement a subclass of `KneeSegmentationModel` (see the abstract
   class below) that loads your trained weights (e.g. `torch.load(...)`)
   in `__init__` and implements `forward()` / `predict()` to return
   real per-pixel femur / tibia / medial-meniscus masks.
2. In `get_segmentation_model()`, change `MODE` to "trained_model" and
   return an instance of your subclass instead of the mock.
3. No other file needs to change - `main.py` and the measurement
   services only depend on the `segment_knee()` function's output
   contract (a dict with femur_mask / tibia_mask / medial_meniscus_mask).
"""

from abc import ABC, abstractmethod
from typing import Dict
import numpy as np
import cv2
import torch
import torch.nn as nn

# Set to "trained_model" once a real trained model is wired in via
# get_segmentation_model(). Left as "demo_mock" by default so the
# system never silently pretends mock output is a real prediction.
MODE = "demo_mock"


class KneeSegmentationModel(ABC, nn.Module):
    """
    Abstract interface that any real trained segmentation model must
    implement. A typical real implementation would be a U-Net / nnU-Net
    style encoder-decoder trained on annotated knee MRI or X-ray slices.
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """Return raw per-class logits/probability maps."""
        raise NotImplementedError

    @abstractmethod
    def predict(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Run inference on a single image (H x W or H x W x C numpy array)
        and return a dict of binary masks:
            {
                "femur_mask": np.ndarray[H, W] (0/1),
                "tibia_mask": np.ndarray[H, W] (0/1),
                "medial_meniscus_mask": np.ndarray[H, W] (0/1),
            }
        """
        raise NotImplementedError


class ExampleUNetPlaceholder(KneeSegmentationModel):
    """
    Skeleton of what a real trained model class looks like structurally.
    This is NOT trained and NOT used by default (MODE stays "demo_mock").
    It is provided so the architecture required is obvious when you are
    ready to plug in real weights.
    """

    def __init__(self, weights_path: str = None):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="nearest"),
            nn.Conv2d(32, 3, 3, padding=1),  # 3 output channels: femur, tibia, meniscus
        )
        if weights_path:
            # Real usage: self.load_state_dict(torch.load(weights_path, map_location="cpu"))
            raise NotImplementedError(
                "No trained weights provided. Load your own trained "
                "checkpoint here before using this class."
            )

    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        x = self.encoder(image_tensor)
        x = self.decoder(x)
        return torch.sigmoid(x)

    def predict(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        raise NotImplementedError(
            "ExampleUNetPlaceholder has no trained weights. This class "
            "is a structural example only - do not use for real inference."
        )


class MockKneeSegmentationModel(KneeSegmentationModel):
    """
    DEMO / MOCK segmentation.

    Produces PLACEHOLDER geometric region masks derived from simple
    image thresholding and fixed anatomical-region heuristics (e.g.
    "the meniscus is roughly in the joint space between upper and
    lower bone regions"). This is used ONLY so the pipeline can be
    demoed without real annotated training data. It must never be
    presented to a user as a real diagnostic segmentation.
    """

    def __init__(self):
        super().__init__()

    def forward(self, image_tensor: torch.Tensor) -> torch.Tensor:
        # Not a real learned forward pass - present only to satisfy
        # the nn.Module interface contract.
        return torch.zeros_like(image_tensor)

    def predict(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        h, w = gray.shape

        # Simple Otsu threshold to separate brighter (bone-like) regions
        # from darker (soft tissue / joint space) regions. This is a
        # crude heuristic, NOT real bone segmentation.
        _, bone_mask = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Heuristic split: upper half of the bright mask = femur,
        # lower half = tibia (assumes a roughly vertical knee image).
        femur_mask = np.zeros((h, w), dtype=np.uint8)
        tibia_mask = np.zeros((h, w), dtype=np.uint8)
        midline = h // 2
        femur_mask[:midline, :] = bone_mask[:midline, :]
        tibia_mask[midline:, :] = bone_mask[midline:, :]

        # Meniscus heuristic: a thin band around the joint space
        # (midline), restricted to the medial (one side) portion of
        # the image width, wherever the region is NOT already bone.
        band_half_thickness = max(2, h // 60)
        meniscus_mask = np.zeros((h, w), dtype=np.uint8)
        medial_col_end = w // 2  # "medial" = inner half, assumed left side here
        row_start = max(0, midline - band_half_thickness)
        row_end = min(h, midline + band_half_thickness)
        meniscus_mask[row_start:row_end, :medial_col_end] = 1
        # Remove overlap with bone masks so meniscus sits strictly in
        # the joint space between femur and tibia.
        meniscus_mask[bone_mask.astype(bool)] = 0

        return {
            "femur_mask": femur_mask,
            "tibia_mask": tibia_mask,
            "medial_meniscus_mask": meniscus_mask,
        }


_model_instance = None


def get_segmentation_model() -> KneeSegmentationModel:
    """
    Factory that returns the active segmentation model based on MODE.
    Swap MODE to "trained_model" and return your real subclass instance
    once trained weights are available.
    """
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if MODE == "trained_model":
        # Replace with your real trained model, e.g.:
        # _model_instance = ExampleUNetPlaceholder(weights_path="weights/knee_unet.pt")
        raise RuntimeError(
            "MODE is set to 'trained_model' but no real model is wired "
            "in yet. Update get_segmentation_model() in segmentation.py."
        )
    else:
        _model_instance = MockKneeSegmentationModel()

    return _model_instance


def segment_knee(image: np.ndarray) -> Dict:
    """
    Public entry point used by the rest of the pipeline.

    Returns:
        {
            "femur_mask": np.ndarray[H, W] (0/1),
            "tibia_mask": np.ndarray[H, W] (0/1),
            "medial_meniscus_mask": np.ndarray[H, W] (0/1),
            "mode": "demo_mock" | "trained_model"
        }
    """
    model = get_segmentation_model()
    masks = model.predict(image)
    masks["mode"] = MODE
    return masks