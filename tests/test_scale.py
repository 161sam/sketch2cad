import pytest
from sketch2cad.models import PipelineConfig
from sketch2cad.scale_reference import compute_mm_per_px


def test_scale_from_ref():
    cfg = PipelineConfig(input_path="in.png", output_dxf="out.dxf", ref_mm=100.0, ref_px=500.0)
    assert compute_mm_per_px(cfg) == pytest.approx(0.2)


def test_scale_missing_ref_raises():
    cfg = PipelineConfig(input_path="in.png", output_dxf="out.dxf")
    with pytest.raises(ValueError):
        compute_mm_per_px(cfg)
