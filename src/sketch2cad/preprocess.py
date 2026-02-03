from __future__ import annotations

import cv2
import numpy as np


def preprocess_to_binary(
    bgr: np.ndarray,
    *,
    blur_ksize: int = 5,
    block_size: int = 41,
    c: int = 7,
    morph_kernel: int = 3,
    morph_iters: int = 1,
) -> np.ndarray:
    """
    Convert BGR image to binary mask (ink=255, background=0).
    Steps:
      - grayscale
      - gaussian blur
      - adaptive threshold (inverted)
      - optional morphology (close) to connect strokes (only if morph_iters > 0)
    """
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    if block_size % 2 == 0:
        block_size += 1
    block_size = max(block_size, 3)

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        c,
    )

    if morph_iters and morph_iters > 0 and morph_kernel and morph_kernel > 1:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel, morph_kernel))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, k, iterations=morph_iters)

    return binary
