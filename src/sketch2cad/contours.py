from __future__ import annotations

import cv2
import numpy as np


def filter_contours(binary: np.ndarray, min_area: int = 50) -> np.ndarray:
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cleaned = np.zeros_like(binary)
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(cleaned, [c], -1, 255, thickness=cv2.FILLED)
    return cleaned


def split_outer_holes_masks(
    binary: np.ndarray,
    gray: np.ndarray | None = None,
    *,
    min_area: int = 80,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Robust split:
      - outer_mask: filled external contours from binary (ink=255)
      - holes_mask: inferred from brightness inside outer (gray), NOT from ~binary

    Reason:
      Adaptive threshold can incorrectly mark bright holes inside a filled region as ink in binary.
      Using ~binary would then erase holes.
    """
    # Outer mask from ink
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    outer = np.zeros_like(binary)
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(outer, [c], -1, 255, thickness=cv2.FILLED)

    if gray is None:
        inv = cv2.bitwise_not(binary)
        holes_raw = cv2.bitwise_and(outer, inv)
        return outer, _cleanup_mask(holes_raw, min_area=min_area)

    # Only consider pixels inside outer area
    vals = gray[outer > 0]
    if vals.size < 50:
        inv = cv2.bitwise_not(binary)
        holes_raw = cv2.bitwise_and(outer, inv)
        return outer, _cleanup_mask(holes_raw, min_area=min_area)

    # Otsu on gray values inside outer:
    # holes are bright => keep bright regions
    masked = cv2.bitwise_and(gray, gray, mask=outer)
    _t, holes_raw = cv2.threshold(masked, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    holes_raw = cv2.bitwise_and(holes_raw, outer)

    holes = _cleanup_mask(holes_raw, min_area=min_area)

    # Fallback: if Otsu produced nothing (rare), use a high fixed threshold
    if holes.max() == 0:
        holes_raw2 = cv2.inRange(masked, 200, 255)  # very bright pixels
        holes_raw2 = cv2.bitwise_and(holes_raw2, outer)
        holes = _cleanup_mask(holes_raw2, min_area=min_area)

    return outer, holes


def _cleanup_mask(mask: np.ndarray, *, min_area: int) -> np.ndarray:
    cleaned = np.zeros_like(mask)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) >= min_area:
            cv2.drawContours(cleaned, [c], -1, 255, thickness=cv2.FILLED)
    return cleaned
