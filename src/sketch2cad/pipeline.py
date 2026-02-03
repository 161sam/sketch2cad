from __future__ import annotations

import json
import traceback
from pathlib import Path

import cv2

from .contours import filter_contours, split_outer_holes_masks
from .export_dxf import export_paths_to_dxf
from .models import PipelineConfig, Report
from .preprocess import preprocess_to_binary
from .scale_reference import compute_mm_per_px
from .vectorize_potrace import vectorize_with_potrace


def run_pipeline(cfg: PipelineConfig) -> Report:
    errors: list[str] = []
    try:
        bgr = cv2.imread(cfg.input_path, cv2.IMREAD_COLOR)
        if bgr is None:
            raise FileNotFoundError(cfg.input_path)

        binary = preprocess_to_binary(
            bgr,
            blur_ksize=cfg.blur_ksize,
            block_size=cfg.adaptive_block_size,
            c=cfg.adaptive_c,
            morph_kernel=cfg.morph_kernel,
            morph_iters=cfg.morph_iters,
        )

        if cfg.use_contours_filter:
            binary = filter_contours(binary, min_area=50)

        mm_per_px = compute_mm_per_px(cfg)

        debug_outer_svg = None
        debug_holes_svg = None
        if cfg.debug_dump:
            Path(cfg.debug_dir).mkdir(parents=True, exist_ok=True)
            debug_bin = Path(cfg.debug_dir) / "binary.png"
            cv2.imwrite(str(debug_bin), binary)
            debug_outer_svg = str(Path(cfg.debug_dir) / "potrace_outline.svg")
            debug_holes_svg = str(Path(cfg.debug_dir) / "potrace_holes.svg")

        # Split into outer and holes masks (both ink=255)
        outer_mask, holes_mask = split_outer_holes_masks(binary, min_area=120)

        if cfg.debug_dump:
            cv2.imwrite(str(Path(cfg.debug_dir) / "mask_outer.png"), outer_mask)
            cv2.imwrite(str(Path(cfg.debug_dir) / "mask_holes.png"), holes_mask)

        # Vectorize separately to keep layer semantics
        paths_outline = vectorize_with_potrace(outer_mask, debug_svg_path=debug_outer_svg)
        for p in paths_outline:
            p.layer = "OUTLINE"

        paths_holes = []
        if holes_mask is not None and holes_mask.max() > 0:
            paths_holes = vectorize_with_potrace(holes_mask, debug_svg_path=debug_holes_svg)
            for p in paths_holes:
                p.layer = "HOLES"

        paths = paths_outline + paths_holes

        export_paths_to_dxf(paths, cfg.output_dxf, scale=mm_per_px)

        h, w = binary.shape[:2]
        rep = Report(
            status="ok",
            input_path=cfg.input_path,
            output_dxf=cfg.output_dxf,
            width=w,
            height=h,
            mm_per_px=mm_per_px,
            num_paths=len(paths),
            errors=[],
        )
        _write_report(cfg.output_dxf, rep)
        return rep

    except Exception as e:
        msg = str(e).strip()
        if not msg:
            msg = repr(e)
        errors.append(msg)
        errors.append(
            "traceback:\n" + "".join(traceback.format_exception(type(e), e, e.__traceback__))
        )

        rep = Report(
            status="error",
            input_path=cfg.input_path,
            output_dxf=cfg.output_dxf,
            width=0,
            height=0,
            mm_per_px=None,
            num_paths=0,
            errors=errors,
        )
        _write_report(cfg.output_dxf, rep)
        return rep


def _write_report(output_dxf: str, report: Report) -> None:
    out = Path(output_dxf)
    report_path = out.with_suffix(out.suffix + ".report.json")
    report_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

