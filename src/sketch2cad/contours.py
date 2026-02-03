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


def split_outer_holes_masks(binary: np.ndarray, min_area: int = 80) -> tuple[np.ndarray, np.ndarray]:
    """
    Split a binary mask (ink=255) into:
      - outer_mask: filled outer contours
      - holes_mask: filled hole contours (children in CCOMP hierarchy)

    Uses RETR_CCOMP hierarchy:
      hierarchy[i][3] == -1  => outer contour
      hierarchy[i][3] != -1  => hole (child)
    """
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    outer = np.zeros_like(binary)
    holes = np.zeros_like(binary)

    if hierarchy is None or len(contours) == 0:
        return outer, holes

    hier = hierarchy[0]
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if area < min_area:
            continue

        parent = hier[i][3]
        if parent == -1:
            cv2.drawContours(outer, [c], -1, 255, thickness=cv2.FILLED)
        else:
            cv2.drawContours(holes, [c], -1, 255, thickness=cv2.FILLED)

    return outer, holes

