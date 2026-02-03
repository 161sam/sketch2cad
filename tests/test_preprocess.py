import numpy as np
from sketch2cad.preprocess import preprocess_to_binary


def test_preprocess_returns_binary():
    # Simple synthetic image: white background with black line
    bgr = np.full((100, 100, 3), 255, dtype=np.uint8)
    bgr[50:52, 10:90] = 0
    bw = preprocess_to_binary(bgr, blur_ksize=3, block_size=21, c=5, morph_kernel=3, morph_iters=1)
    assert bw.shape == (100, 100)
    assert bw.dtype == np.uint8
