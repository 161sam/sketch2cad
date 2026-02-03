from pathlib import Path
import ezdxf
from sketch2cad.export_dxf import export_paths_to_dxf


def test_export_writes_dxf(tmp_path: Path):
    out = tmp_path / "out.dxf"
    export_paths_to_dxf([], str(out), scale=1.0)
    assert out.exists()

    doc = ezdxf.readfile(str(out))
    assert doc is not None

