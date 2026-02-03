from __future__ import annotations

import cv2
import numpy as np


def filter_contours(binary: np.ndarray, min_area: int = 50) -> np.ndarray:
    """
    Removes small artifacts using contour area thresholding.
    Returns a cleaned binary image (ink=255).
    """
    contours, _hier = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    cleaned = np.zeros_like(binary)

    for c in contours:
        area = cv2.contourArea(c)
        if area >= min_area:
            cv2.drawContours(cleaned, [c], -1, 255, thickness=cv2.FILLED)

    return cleaned
