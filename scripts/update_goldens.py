#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from sketch2cad.models import PipelineConfig
from sketch2cad.pipeline import run_pipeline
from sketch2cad.metrics import compute_dxf_metrics


FIXTURES_DIR = Path("tests/fixtures")


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


def main() -> int:
    if not FIXTURES_DIR.exists():
        print(f"Fixtures dir not found: {FIXTURES_DIR}")
        return 1

    fixture_dirs = [p for p in FIXTURES_DIR.iterdir() if p.is_dir()]
    if not fixture_dirs:
        print("No fixtures found.")
        return 0

    failed = 0

    for fdir in sorted(fixture_dirs):
        meta_path = fdir / "meta.json"
        input_path = fdir / "input.png"
        if not meta_path.exists() or not input_path.exists():
            print(f"Skipping {fdir.name}: missing meta.json or input.png")
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        ref_mm = float(meta.get("ref_mm"))
        ref_px = float(meta.get("ref_px"))

        out_dxf = fdir / "golden_out.dxf"
        debug_dir = fdir / "_debug"

        cfg = PipelineConfig(
            input_path=str(input_path),
            output_dxf=str(out_dxf),
            ref_mm=ref_mm,
            ref_px=ref_px,
            debug_dump=True,
            debug_dir=str(debug_dir),
        )
        cfg = _apply_preprocess_overrides(cfg, meta)

        rep = run_pipeline(cfg)
        if rep.status != "ok":
            failed += 1
            print(f"❌ {fdir.name}: pipeline failed")
            for e in rep.errors:
                print(e)
            continue

        metrics = compute_dxf_metrics(str(out_dxf))
        (fdir / "golden_metrics.json").write_text(
            json.dumps(metrics.to_dict(), indent=2),
            encoding="utf-8",
        )
        print(f"✅ {fdir.name}: wrote golden_metrics.json")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

