from __future__ import annotations

from typing import List

import ezdxf

from .models import VectorPath


def export_paths_to_dxf(
    paths: List[VectorPath],
    out_path: str,
    *,
    scale: float,
) -> None:
    """
    Exports VectorPaths to DXF.
    For now, paths may be empty (until SVG parsing is implemented).
    """
    if scale <= 0:
        raise ValueError("scale must be > 0")

    doc = ezdxf.new(dxfversion="R2018")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    # Ensure layers exist
    layers = {p.layer for p in paths} | {"OUTLINE", "HOLES", "REF"}
    for layer in layers:
        if layer not in doc.layers:
            doc.layers.new(name=layer)

    # Placeholder: no geometry until Issue #7 is implemented.
    # Later: add LWPOLYLINE or SPLINE entities.

    doc.saveas(out_path)
