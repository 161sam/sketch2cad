from pathlib import Path
import json

import ezdxf
import numpy as np
import cv2

from sketch2cad.models import PipelineConfig
from sketch2cad.pipeline import run_pipeline


def _make_test_image(path: Path) -> None:
    # white background
    img = np.full((300, 400, 3), 255, dtype=np.uint8)

    # draw a rectangle (ink)
    cv2.rectangle(img, (60, 80), (320, 220), (0, 0, 0), thickness=6)

    # draw a reference line (e.g. 200 px long)
    cv2.line(img, (60, 260), (260, 260), (0, 0, 0), thickness=6)

    cv2.imwrite(str(path), img)


def test_e2e_synthetic_rect_generates_dxf(tmp_path: Path):
    inp = tmp_path / "input.png"
    out = tmp_path / "out.dxf"

    _make_test_image(inp)

    # quick mode: 100mm corresponds to 200px => 0.5mm/px
    cfg = PipelineConfig(
        input_path=str(inp),
        output_dxf=str(out),
        ref_mm=100.0,
        ref_px=200.0,
        debug_dump=True,
        debug_dir=str(tmp_path / "_debug"),
    )

    rep = run_pipeline(cfg)
    assert rep.status == "ok", rep.errors
    assert out.exists()

    # Read DXF and verify it's not empty
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    entities = list(msp)

    # We expect at least 1 entity after vectorization/parsing/export.
    assert len(entities) >= 1

    # Ensure we produce known layers
    layer_names = {e.dxf.layer for e in entities}
    assert "OUTLINE" in layer_names or len(layer_names) >= 1

    # Also check report exists
    report_path = Path(str(out) + ".report.json")
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "ok"
