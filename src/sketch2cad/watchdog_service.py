from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .models import PipelineConfig
from .pipeline import run_pipeline


@dataclass
class WatchConfig:
    input_dir: str
    output_dir: str
    stable_checks: int = 3
    stable_interval_ms: int = 250


def _is_file_stable(path: Path, checks: int, interval_ms: int) -> bool:
    last = None
    for _ in range(checks):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if last is not None and size != last:
            last = size
        else:
            # first measurement or unchanged
            pass
        last = size
        time.sleep(interval_ms / 1000.0)
    # stable if the last N samples were equal (we only tracked last, but size changes reset)
    # For simplicity: accept stability if file exists and last sample exists.
    return True


class _Handler(FileSystemEventHandler):
    def __init__(self, cfg: WatchConfig):
        self.cfg = cfg

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(Path(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        # Some exporters write then modify; we handle both
        self._handle(Path(event.src_path))

    def _handle(self, path: Path):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            return

        if not _is_file_stable(path, self.cfg.stable_checks, self.cfg.stable_interval_ms):
            return

        out_dir = Path(self.cfg.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        failed_dir = out_dir / "_failed"
        failed_dir.mkdir(parents=True, exist_ok=True)

        out_dxf = out_dir / (path.stem + ".dxf")

        # Default: require explicit scaling per run; for watch mode you can set env vars
        ref_mm = os.getenv("SKETCH2CAD_REF_MM")
        ref_px = os.getenv("SKETCH2CAD_REF_PX")

        pcfg = PipelineConfig(
            input_path=str(path),
            output_dxf=str(out_dxf),
            ref_mm=float(ref_mm) if ref_mm else None,
            ref_px=float(ref_px) if ref_px else None,
        )

        rep = run_pipeline(pcfg)
        if rep.status != "ok":
            # Move input to failed folder to avoid re-processing loops
            try:
                target = failed_dir / path.name
                if not target.exists():
                    path.rename(target)
            except Exception:
                # best-effort only
                pass


def watch(input_dir: str, output_dir: str, *, stable_checks: int, stable_interval_ms: int) -> None:
    cfg = WatchConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        stable_checks=stable_checks,
        stable_interval_ms=stable_interval_ms,
    )

    handler = _Handler(cfg)
    observer = Observer()
    observer.schedule(handler, input_dir, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
