from __future__ import annotations

from .models import PipelineConfig


def compute_mm_per_px(cfg: PipelineConfig) -> float:
    """
    MVP scaling:
    - Prefer explicit mm_per_px if set
    - Else require ref_mm and ref_px to compute mm/px
    """
    if cfg.mm_per_px is not None:
        if cfg.mm_per_px <= 0:
            raise ValueError("mm_per_px must be > 0")
        return float(cfg.mm_per_px)

    if cfg.ref_mm is None or cfg.ref_px is None:
        raise ValueError(
            "Missing scaling reference: provide --ref-mm and --ref-px (MVP quick mode) "
            "or set mm_per_px directly."
        )

    if cfg.ref_mm <= 0 or cfg.ref_px <= 0:
        raise ValueError("ref_mm and ref_px must be > 0")

    return float(cfg.ref_mm) / float(cfg.ref_px)
