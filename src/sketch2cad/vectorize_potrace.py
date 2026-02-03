from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from .models import VectorPath


def _ensure_potrace() -> None:
    if shutil.which("potrace") is None:
        raise RuntimeError(
            "potrace not found. Install on Ubuntu/Debian: sudo apt install -y potrace"
        )


def binary_to_svg(binary: np.ndarray, out_svg: Path) -> None:
    """
    Uses potrace CLI to convert a binary bitmap into an SVG file.
    """
    _ensure_potrace()
    out_svg.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        inp = td_path / "input.pbm"

        # Write binary bitmap; potrace handles PBM/PGM/PPM/PNM.
        # OpenCV writes PGM reliably; keep extension .pgm.
        cv2.imwrite(str(inp.with_suffix(".pgm")), binary)
        inp = inp.with_suffix(".pgm")

        cmd = ["potrace", str(inp), "-s", "-o", str(out_svg)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(
                f"potrace failed (rc={proc.returncode}): {proc.stderr.strip()}"
            )


def svg_to_paths(svg_path: Path, *, layer: str = "OUTLINE") -> List[VectorPath]:
    """
    Placeholder for SVG path parsing (Phase 1.3 / Issue #7).
    We will later parse SVG 'path d=' into VectorPath segments.

    For now, return an empty list to keep the pipeline runnable.
    """
    _ = svg_path.read_text(encoding="utf-8", errors="replace")
    return []


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
            Path(debug_svg_path).write_text(svg.read_text(encoding="utf-8"), encoding="utf-8")

        return svg_to_paths(svg)
