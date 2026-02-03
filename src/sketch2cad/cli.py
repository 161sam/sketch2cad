from __future__ import annotations

import os
from pathlib import Path
import typer
from dotenv import load_dotenv

from .models import PipelineConfig
from .pipeline import run_pipeline
from .watchdog_service import watch

app = typer.Typer(help="Sketch2CAD: sketch image -> DXF (MVP scaffold)")


@app.callback()
def _main():
    # Load .env if present
    if Path(".env").exists():
        load_dotenv(".env")


@app.command()
def run(
    input_path: str = typer.Argument(..., help="Input image file (png/jpg)"),
    output: str = typer.Option("out.dxf", "--output", "-o", help="Output DXF path"),
    ref_mm: float = typer.Option(None, "--ref-mm", help="Reference length in mm"),
    ref_px: float = typer.Option(None, "--ref-px", help="Reference length in pixels (MVP quick mode)"),
    blur_ksize: int = typer.Option(5, help="Gaussian blur kernel size"),
    block_size: int = typer.Option(41, help="Adaptive threshold block size (odd)"),
    adaptive_c: int = typer.Option(7, help="Adaptive threshold C"),
    morph_kernel: int = typer.Option(3, help="Morphology kernel size"),
    morph_iters: int = typer.Option(1, help="Morphology iterations"),
    no_contours_filter: bool = typer.Option(False, help="Disable contour filtering"),
    debug: bool = typer.Option(False, help="Dump debug artifacts"),
    debug_dir: str = typer.Option("./examples/output/_debug", help="Debug output dir"),
):
    cfg = PipelineConfig(
        input_path=input_path,
        output_dxf=output,
        ref_mm=ref_mm,
        ref_px=ref_px,
        blur_ksize=blur_ksize,
        adaptive_block_size=block_size,
        adaptive_c=adaptive_c,
        morph_kernel=morph_kernel,
        morph_iters=morph_iters,
        use_contours_filter=not no_contours_filter,
        debug_dump=debug,
        debug_dir=debug_dir,
    )

    rep = run_pipeline(cfg)
    if rep.status != "ok":
        typer.echo("❌ Pipeline failed:")
        for e in rep.errors:
            typer.echo(f"  - {e}")
        raise typer.Exit(code=1)

    typer.echo(f"✅ DXF written: {output}")
    typer.echo(f"   mm_per_px: {rep.mm_per_px}")
    typer.echo(f"   paths: {rep.num_paths}")
    typer.echo(f"   report: {output}.report.json")


@app.command()
def watch_cmd(
    input_dir: str = typer.Argument(None, help="Input directory (default: env SKETCH2CAD_INPUT_DIR)"),
    output_dir: str = typer.Argument(None, help="Output directory (default: env SKETCH2CAD_OUTPUT_DIR)"),
    stable_checks: int = typer.Option(None, help="Number of stable-size checks"),
    stable_interval_ms: int = typer.Option(None, help="Interval between checks (ms)"),
):
    in_dir = input_dir or os.getenv("SKETCH2CAD_INPUT_DIR", "./examples/input")
    out_dir = output_dir or os.getenv("SKETCH2CAD_OUTPUT_DIR", "./examples/output")

    sc = stable_checks if stable_checks is not None else int(os.getenv("SKETCH2CAD_STABLE_CHECKS", "3"))
    si = stable_interval_ms if stable_interval_ms is not None else int(os.getenv("SKETCH2CAD_STABLE_INTERVAL_MS", "250"))

    Path(in_dir).mkdir(parents=True, exist_ok=True)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    typer.echo(f"👀 Watching: {in_dir} -> {out_dir}")
    typer.echo("   (Ctrl+C to stop)")
    watch(in_dir, out_dir, stable_checks=sc, stable_interval_ms=si)


# "watch" command name in CLI
app.command("watch")(watch_cmd)
