from __future__ import annotations

import cv2
import numpy as np


def preprocess_to_binary(
    bgr: np.ndarray,
    blur_ksize: int,
    block_size: int,
    c: int,
    morph_kernel: int,
    morph_iters: int,
) -> np.ndarray:
    """
    Converts BGR image to binary (ink=255, background=0).
    Robust against shadows via adaptive thresholding.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    if blur_ksize and blur_ksize > 1:
        k = blur_ksize if blur_ksize % 2 == 1 else blur_ksize + 1
        gray = cv2.GaussianBlur(gray, (k, k), 0)

    bs = block_size if block_size % 2 == 1 else block_size + 1
    bw = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        bs,
        c,
    )

    if morph_kernel and morph_kernel > 1:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morph_kernel, morph_kernel)
        )
        it_close = max(1, morph_iters)
        bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=it_close)
        bw = cv2.morphologyEx(
            bw, cv2.MORPH_OPEN, kernel, iterations=max(1, morph_iters // 2)
        )

    return bw
