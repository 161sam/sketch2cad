from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

Point = Tuple[float, float]


@dataclass
class PathSegment:
    """
    Minimal segment model.
    kind: "line" | "cubic_bezier" | "quad_bezier"
    pts: list of points (interpretation depends on kind)
    """
    kind: str
    pts: List[Point]


@dataclass
class VectorPath:
    """
    A vector path consisting of segments. Coordinates are in pixel space by default.
    """
    segments: List[PathSegment]
    is_closed: bool = False
    layer: str = "OUTLINE"


@dataclass
class PipelineConfig:
    input_path: str
    output_dxf: str

    # Preprocess params
    blur_ksize: int = 5
    adaptive_block_size: int = 41
    adaptive_c: int = 7

    morph_kernel: int = 3
    morph_iters: int = 1

    # Scaling (MVP: reference in image)
    ref_mm: Optional[float] = None
    ref_px: Optional[float] = None
    mm_per_px: Optional[float] = None

    # Optional toggles
    use_contours_filter: bool = True
    debug_dump: bool = False
    debug_dir: str = "./examples/output/_debug"


@dataclass
class Report:
    status: str  # "ok" | "error"
    input_path: str
    output_dxf: str
    width: int
    height: int
    mm_per_px: Optional[float]
    num_paths: int
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
