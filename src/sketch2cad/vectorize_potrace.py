from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from xml.etree import ElementTree as ET

import cv2
import numpy as np
from svgpathtools import svg2paths2, Line, CubicBezier, QuadraticBezier

from .models import PathSegment, VectorPath

# -----------------------------
# SVG transform handling
# -----------------------------

Affine = Tuple[float, float, float, float, float, float]
# matrix:
# [ a c e ]
# [ b d f ]
# [ 0 0 1 ]


def _affine_identity() -> Affine:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _affine_mul(m1: Affine, m2: Affine) -> Affine:
    # m1 ∘ m2 (apply m2 first, then m1)
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _affine_apply(m: Affine, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


_transform_re = re.compile(r"(translate|scale|matrix)\s*\(([^)]*)\)")


def _parse_transform_list(transform: str) -> Affine:
    """
    Parses a limited subset of SVG transforms:
      - translate(tx[,ty])
      - scale(sx[,sy])
      - matrix(a,b,c,d,e,f)
    Returns a single affine matrix.
    SVG applies transforms from right to left. For a list "T1 T2", points are transformed by T2 then T1.
    We compose accordingly.
    """
    transform = transform.strip()
    if not transform:
        return _affine_identity()

    mats: list[Affine] = []
    for m in _transform_re.finditer(transform):
        kind = m.group(1)
        args = [float(x) for x in re.split(r"[ ,]+", m.group(2).strip()) if x]

        if kind == "translate":
            tx = args[0] if len(args) >= 1 else 0.0
            ty = args[1] if len(args) >= 2 else 0.0
            mats.append((1.0, 0.0, 0.0, 1.0, tx, ty))

        elif kind == "scale":
            sx = args[0] if len(args) >= 1 else 1.0
            sy = args[1] if len(args) >= 2 else sx
            mats.append((sx, 0.0, 0.0, sy, 0.0, 0.0))

        elif kind == "matrix":
            if len(args) != 6:
                continue
            a, b, c, d, e, f = args
            mats.append((a, b, c, d, e, f))

    # Compose right-to-left
    out = _affine_identity()
    for m in reversed(mats):
        out = _affine_mul(m, out)
    return out


def _extract_group_transform(svg_text: str) -> Affine:
    """
    Potrace SVG commonly uses a <g transform="translate(... ) scale(... )"> wrapper.
    We try to extract the first <g> transform if present.
    """
    try:
        root = ET.fromstring(svg_text)
    except Exception:
        return _affine_identity()

    for el in root.iter():
        if el.tag.endswith("g") and "transform" in el.attrib:
            return _parse_transform_list(el.attrib.get("transform", ""))
    return _affine_identity()


# -----------------------------
# Potrace integration
# -----------------------------


def _ensure_potrace() -> None:
    if shutil.which("potrace") is None:
        raise RuntimeError(
            "potrace not found. Install on Ubuntu/Debian: sudo apt install -y potrace"
        )


def binary_to_svg(binary: np.ndarray, out_svg: Path) -> None:
    """
    Uses potrace CLI to convert a binary bitmap into an SVG file.
    We set unit (-u 1) to reduce surprising scaling factors.

    Important: Potrace expects black shapes on white background.
    Our preprocess produces ink=255 on background=0 (THRESH_BINARY_INV),
    so we invert before feeding potrace.
    """
    _ensure_potrace()
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        inp = td_path / "input.pgm"

        inv = 255 - binary
        cv2.imwrite(str(inp), inv)

        cmd = ["potrace", str(inp), "-s", "-u", "1", "-o", str(out_svg)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"potrace failed (rc={proc.returncode}): {proc.stderr.strip()}"
            )


def svg_to_paths(svg_path: Path, *, layer: str = "OUTLINE") -> List[VectorPath]:
    """
    Parse SVG paths (Potrace output) to VectorPaths.

    We:
    - read svg text
    - extract group transform (common in potrace output)
    - parse paths using svgpathtools
    - convert segments to our internal representation
    - apply group transform to all points
    """
    svg_text = svg_path.read_text(encoding="utf-8", errors="replace")
    gxf = _extract_group_transform(svg_text)

    paths, path_attrs, _svg_attrs = svg2paths2(str(svg_path))

    out: list[VectorPath] = []
    for p, attrs in zip(paths, path_attrs):
        lp = layer

        segments: list[PathSegment] = []
        for seg in p:
            if isinstance(seg, Line):
                x0, y0 = seg.start.real, seg.start.imag
                x1, y1 = seg.end.real, seg.end.imag
                x0, y0 = _affine_apply(gxf, float(x0), float(y0))
                x1, y1 = _affine_apply(gxf, float(x1), float(y1))
                segments.append(PathSegment(kind="line", pts=[(x0, y0), (x1, y1)]))

            elif isinstance(seg, CubicBezier):
                pts = [
                    (seg.start.real, seg.start.imag),
                    (seg.control1.real, seg.control1.imag),
                    (seg.control2.real, seg.control2.imag),
                    (seg.end.real, seg.end.imag),
                ]
                pts2 = [_affine_apply(gxf, float(x), float(y)) for (x, y) in pts]
                segments.append(PathSegment(kind="cubic_bezier", pts=pts2))

            elif isinstance(seg, QuadraticBezier):
                pts = [
                    (seg.start.real, seg.start.imag),
                    (seg.control.real, seg.control.imag),
                    (seg.end.real, seg.end.imag),
                ]
                pts2 = [_affine_apply(gxf, float(x), float(y)) for (x, y) in pts]
                segments.append(PathSegment(kind="quad_bezier", pts=pts2))

            else:
                x0, y0 = seg.start.real, seg.start.imag
                x1, y1 = seg.end.real, seg.end.imag
                x0, y0 = _affine_apply(gxf, float(x0), float(y0))
                x1, y1 = _affine_apply(gxf, float(x1), float(y1))
                segments.append(PathSegment(kind="line", pts=[(x0, y0), (x1, y1)]))

        out.append(VectorPath(segments=segments, is_closed=p.isclosed(), layer=lp))

    return out


def vectorize_with_potrace(
    binary: np.ndarray,
    debug_svg_path: Optional[str] = None,
) -> List[VectorPath]:
    """
    End-to-end vectorization:
    binary -> (potrace) -> svg -> (parse) -> VectorPath list
    """
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        svg = td_path / "out.svg"
        binary_to_svg(binary, svg)

        if debug_svg_path:
            Path(debug_svg_path).parent.mkdir(parents=True, exist_ok=True)
            Path(debug_svg_path).write_text(
                svg.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )

        return svg_to_paths(svg)
