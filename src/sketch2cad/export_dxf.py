from __future__ import annotations

from typing import List, Tuple

import ezdxf

from .models import PathSegment, VectorPath


Point = Tuple[float, float]


def _sample_cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, n: int) -> List[Point]:
    # uniform sampling t in [0..1]
    pts: list[Point] = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = (mt**3) * p0[0] + 3 * (mt**2) * t * p1[0] + 3 * mt * (t**2) * p2[0] + (t**3) * p3[0]
        y = (mt**3) * p0[1] + 3 * (mt**2) * t * p1[1] + 3 * mt * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x, y))
    return pts


def _sample_quad_bezier(p0: Point, p1: Point, p2: Point, n: int) -> List[Point]:
    pts: list[Point] = []
    for i in range(n + 1):
        t = i / n
        mt = 1.0 - t
        x = (mt**2) * p0[0] + 2 * mt * t * p1[0] + (t**2) * p2[0]
        y = (mt**2) * p0[1] + 2 * mt * t * p1[1] + (t**2) * p2[1]
        pts.append((x, y))
    return pts


def _segment_to_points(seg: PathSegment, *, samples: int) -> List[Point]:
    if seg.kind == "line":
        return [seg.pts[0], seg.pts[-1]]

    if seg.kind == "cubic_bezier" and len(seg.pts) == 4:
        return _sample_cubic_bezier(seg.pts[0], seg.pts[1], seg.pts[2], seg.pts[3], n=samples)

    if seg.kind == "quad_bezier" and len(seg.pts) == 3:
        return _sample_quad_bezier(seg.pts[0], seg.pts[1], seg.pts[2], n=samples)

    # Fallback
    return [seg.pts[0], seg.pts[-1]]


def export_paths_to_dxf(
    paths: List[VectorPath],
    out_path: str,
    *,
    scale: float,
    bezier_samples: int = 16,
    prefer_splines: bool = True,
) -> None:
    """
    Export VectorPaths to DXF:
    - Lines become LWPOLYLINE
    - Beziers become SPLINE with fit points (sampled)
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

    for vp in paths:
        # Build a point stream (sampled for curves)
        pts: list[Point] = []
        has_curve = False

        for seg in vp.segments:
            seg_pts = _segment_to_points(seg, samples=bezier_samples)

            if seg.kind in {"cubic_bezier", "quad_bezier"}:
                has_curve = True

            # Avoid duplicating boundary points between segments
            if pts and seg_pts:
                if _almost_same(pts[-1], seg_pts[0]):
                    pts.extend(seg_pts[1:])
                else:
                    pts.extend(seg_pts)
            else:
                pts.extend(seg_pts)

        # Apply scaling to mm
        pts_mm = [(x * scale, y * scale) for (x, y) in pts]

        if not pts_mm:
            continue

        attribs = {"layer": vp.layer}

        if prefer_splines and has_curve and len(pts_mm) >= 4:
            # Use spline with fit points (sampled). Close if needed.
            spl = msp.add_spline(fit_points=pts_mm, dxfattribs=attribs)
            if vp.is_closed:
                spl.closed = True
        else:
            # Polyline fallback
            msp.add_lwpolyline(pts_mm, close=vp.is_closed, dxfattribs=attribs)

    doc.saveas(out_path)


def _almost_same(a: Point, b: Point, eps: float = 1e-6) -> bool:
    return abs(a[0] - b[0]) <= eps and abs(a[1] - b[1]) <= eps
