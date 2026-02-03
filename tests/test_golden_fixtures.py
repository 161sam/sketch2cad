from __future__ import annotations

import json
from pathlib import Path

from sketch2cad.models import PipelineConfig
from sketch2cad.pipeline import run_pipeline
from sketch2cad.metrics import compute_dxf_metrics


FIXTURES_DIR = Path("tests/fixtures")


def _assert_bbox_close(b1, b2, abs_tol: float):
    for a, b in zip(b1, b2):
        assert abs(a - b) <= abs_tol, f"bbox mismatch: {b1} vs {b2} (tol={abs_tol})"


def _apply_preprocess_overrides(cfg: PipelineConfig, meta: dict) -> PipelineConfig:
    pp = meta.get("preprocess") or {}
    if not isinstance(pp, dict):
        return cfg
    cfg.blur_ksize = int(pp.get("blur_ksize", cfg.blur_ksize))
    cfg.adaptive_block_size = int(pp.get("adaptive_block_size", cfg.adaptive_block_size))
    cfg.adaptive_c = int(pp.get("adaptive_c", cfg.adaptive_c))
    cfg.morph_kernel = int(pp.get("morph_kernel", cfg.morph_kernel))
    cfg.morph_iters = int(pp.get("morph_iters", cfg.morph_iters))
    return cfg


def test_fixtures_against_goldens(tmp_path: Path):
    assert FIXTURES_DIR.exists()

    for fdir in sorted([p for p in FIXTURES_DIR.iterdir() if p.is_dir()]):
        meta_path = fdir / "meta.json"
        input_path = fdir / "input.png"
        golden_metrics_path = fdir / "golden_metrics.json"

        if not (meta_path.exists() and input_path.exists() and golden_metrics_path.exists()):
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        tol = meta.get("tolerances", {})
        bbox_tol = float(tol.get("bbox_mm_abs", 2.0))

        ref_mm = float(meta["ref_mm"])
        ref_px = float(meta["ref_px"])

        out_dxf = tmp_path / f"{fdir.name}.dxf"
        cfg = PipelineConfig(
            input_path=str(input_path),
            output_dxf=str(out_dxf),
            ref_mm=ref_mm,
            ref_px=ref_px,
            debug_dump=False,
        )
        cfg = _apply_preprocess_overrides(cfg, meta)

        rep = run_pipeline(cfg)
        assert rep.status == "ok", rep.errors

        got = compute_dxf_metrics(str(out_dxf)).to_dict()
        exp = json.loads(golden_metrics_path.read_text(encoding="utf-8"))

        assert got["num_entities"] >= 1
        assert exp["num_entities"] >= 1

        _assert_bbox_close(got["bbox_mm"], exp["bbox_mm"], abs_tol=bbox_tol)

        # Semantic expectation: holes_* fixtures should produce HOLES layer entities
        if fdir.name.startswith("holes_"):
            assert "HOLES" in got["layers"], f"{fdir.name}: expected HOLES layer, got {got[layers]}"
            if fdir.name == "holes_multi":
                assert got["layers"].get("HOLES", 0) >= 2, f"{fdir.name}: expected >=2 HOLES entities, got {got[layers]}"
            if fdir.name == "holes_nested":
                assert got["layers"].get("HOLES", 0) >= 1, f"{fdir.name}: expected >=1 HOLES entity, got {got[layers]}"

