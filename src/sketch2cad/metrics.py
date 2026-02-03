from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple

import ezdxf


BBox = Tuple[float, float, float, float]


@dataclass
class DxfMetrics:
    num_entities: int
    entities_by_type: Dict[str, int]
    layers: Dict[str, int]
    bbox_mm: BBox

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_dxf_metrics(dxf_path: str) -> DxfMetrics:
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    entities = list(msp)

    entities_by_type: Dict[str, int] = {}
    layers: Dict[str, int] = {}

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for e in entities:
        t = e.dxftype()
        entities_by_type[t] = entities_by_type.get(t, 0) + 1
        layer = getattr(e.dxf, "layer", "0")
        layers[layer] = layers.get(layer, 0) + 1

        # Bounding box: handle common entity types we create
        pts = _extract_points(e)
        for x, y in pts:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

    if min_x == float("inf"):
        # no geometry
        min_x = min_y = max_x = max_y = 0.0

    return DxfMetrics(
        num_entities=len(entities),
        entities_by_type=entities_by_type,
        layers=layers,
        bbox_mm=(min_x, min_y, max_x, max_y),
    )


def _extract_points(e) -> list[tuple[float, float]]:
    """
    Best-effort extraction for entities used in this project:
    - LWPOLYLINE: vertices
    - SPLINE: fit points / control points (fallback)
    """
    t = e.dxftype()

    if t == "LWPOLYLINE":
        return [(float(x), float(y)) for x, y, *_ in e.get_points("xyseb")]

    if t == "SPLINE":
        pts = []
        try:
            fit = list(e.fit_points)
            pts.extend([(float(p.x), float(p.y)) for p in fit])
        except Exception:
            pass
        if not pts:
            try:
                ctrl = list(e.control_points)
                pts.extend([(float(p.x), float(p.y)) for p in ctrl])
            except Exception:
                pass
        return pts

    # Unknown: no points
    return []
