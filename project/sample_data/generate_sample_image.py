"""
generate_sample_image.py
--------------------------
Creates a synthetic grayscale PNG that can be used to exercise the
/upload and /analyze endpoints without a real medical image.

This is NOT a real knee X-ray/MRI - it is randomly generated pixel
data solely for pipeline testing (uploading, segmentation demo,
measurement, implant matching). It has no diagnostic meaning.

Usage:
    python3 generate_sample_image.py
"""

import os
import numpy as np
import cv2

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_knee.png")


def main():
    height, width = 400, 300
    # Brighter band in the middle third (roughly "bone-like"), darker
    # elsewhere, plus noise - just enough structure for the demo/mock
    # thresholding segmentation to produce non-trivial masks.
    img = np.random.randint(40, 90, (height, width), dtype=np.uint8)
    img[: height // 2 - 10, :] = np.random.randint(160, 220, (height // 2 - 10, width), dtype=np.uint8)
    img[height // 2 + 10:, :] = np.random.randint(160, 220, (height - (height // 2 + 10), width), dtype=np.uint8)

    cv2.imwrite(OUTPUT_PATH, img)
    print(f"Sample image written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()