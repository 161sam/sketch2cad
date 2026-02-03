# Sketch2CAD

Hands sketched images (e.g. Sketch/Draw App exports) → DXF / STEP.

🚧 Project scaffold – implementation in progress.

See roadmap and issues for details.

---

Sketch2CAD converts hand sketches (e.g. Samsung Flip exports/photos) into CAD-friendly DXF,
and later optionally STEP (3D).

## MVP pipeline (Phase 1)
OpenCV (clean) → Potrace (vectorize) → ezdxf (DXF export)

### Scaling (MVP)
Scaling is done via **reference in the image**:
- recommended: draw a reference line (e.g. 100mm) and provide `--ref-mm` + `--ref-px` (quick mode)
- later (Phase 2/3): auto screen detection using display dimensions, with reference fallback

## Install

System dependency (Ubuntu/Debian):
```bash
sudo apt update && sudo apt install -y potrace
````

Python:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,svg]"
```

## Usage

Single run (MVP quick scaling):

```bash
sketch2cad run examples/input/input.png --output examples/output/out.dxf --ref-mm 100 --ref-px 842
```

Hotfolder:

```bash
sketch2cad watch ./examples/input ./examples/output
```

## Smoke: CLI help

```bash
sketch2cad --help
sketch2cad run --help
sketch2cad watch --help
```
