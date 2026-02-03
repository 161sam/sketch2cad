#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Sketch2CAD – Repository Initializer
# ------------------------------------------------------------

PROJECT_NAME="sketch2cad"
DEFAULT_BRANCH="main"

echo "🚀 Initialisiere Projekt: $PROJECT_NAME"

# ------------------------------------------------------------
# 1. Verzeichnisstruktur
# ------------------------------------------------------------

echo "📁 Erstelle Projektstruktur …"

mkdir -p \
  src/sketch2cad \
  tests/fixtures \
  systemd \
  examples/input \
  examples/output \
  scripts

# ------------------------------------------------------------
# 2. Placeholder-Dateien (bewusst leer oder minimal)
# ------------------------------------------------------------

echo "📄 Erstelle Placeholder-Dateien …"

# Python package
touch src/sketch2cad/__init__.py
touch src/sketch2cad/cli.py
touch src/sketch2cad/pipeline.py
touch src/sketch2cad/preprocess.py
touch src/sketch2cad/contours.py
touch src/sketch2cad/vectorize_potrace.py
touch src/sketch2cad/export_dxf.py
touch src/sketch2cad/scale_reference.py
touch src/sketch2cad/scale_screen.py
touch src/sketch2cad/segment_sam.py
touch src/sketch2cad/cadquery_step.py
touch src/sketch2cad/models.py

# Tests
touch tests/__init__.py
touch tests/test_preprocess.py
touch tests/test_scale.py
touch tests/test_svg_parser.py
touch tests/test_export_dxf.py
touch tests/test_e2e_golden.py

# Fixtures placeholder
touch tests/fixtures/.gitkeep

# Systemd
touch systemd/sketch2cad.service

# Scripts
touch scripts/update_goldens.py

# Root files
touch README.md
touch pyproject.toml
touch .env.example
touch .gitignore
touch LICENSE

# ------------------------------------------------------------
# 3. Minimal .gitignore
# ------------------------------------------------------------

echo "📝 Schreibe .gitignore …"

cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.env

# Build / dist
build/
dist/

# Test artifacts
.pytest_cache/
coverage.xml

# DXF / CAD outputs
*.dxf
*.step

# OS / Editor
.DS_Store
.idea/
.vscode/

# Runtime folders
examples/output/
EOF

# ------------------------------------------------------------
# 4. Minimal README
# ------------------------------------------------------------

echo "📝 Schreibe README.md …"

cat > README.md <<'EOF'
# Sketch2CAD

Hands sketched images (e.g. Samsung Flip exports) → DXF / STEP.

🚧 Project scaffold – implementation in progress.

See roadmap and issues for details.
EOF

# ------------------------------------------------------------
# 5. Lizenz (Apache-2.0, Platzhalter)
# ------------------------------------------------------------

echo "📝 Schreibe LICENSE …"

cat > LICENSE <<'EOF'
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

Copyright (c) 2026
EOF

# ------------------------------------------------------------
# 6. Git initialisieren
# ------------------------------------------------------------

echo "🔧 Initialisiere Git …"

git init
git checkout -b "$DEFAULT_BRANCH"

git add .
git commit -m "chore: initial project scaffold"

# ------------------------------------------------------------
# 7. GitHub Repo via gh erstellen & pushen
# ------------------------------------------------------------

echo "🌍 Erstelle GitHub Repository via gh …"

gh repo create "$PROJECT_NAME" \
  --source=. \
  --public \
  --push \
  --remote=origin

# ------------------------------------------------------------
# Done
# ------------------------------------------------------------

echo "✅ Fertig!"
echo "➡️ Repository ist erstellt, initialisiert und gepusht."
