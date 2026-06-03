#!/usr/bin/env bash
# Build AAIS desktop window executable (Linux) — pywebview shell.
# Output: dist/aais_desktop (not committed to git)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Installing desktop build dependencies..."
python -m pip install -q -e ".[dev,desktop]"

echo "Preparing frontend bundle..."
python -m aais prepare --data-dir "$ROOT/.runtime/aais-data"

echo "Running PyInstaller (desktop window)..."
python -m PyInstaller --onefile --name aais_desktop --clean run_aais_desktop.py \
  --hidden-import=uvicorn \
  --hidden-import=uvicorn.logging \
  --hidden-import=uvicorn.loops \
  --hidden-import=uvicorn.loops.auto \
  --hidden-import=uvicorn.protocols \
  --hidden-import=uvicorn.protocols.http \
  --hidden-import=uvicorn.protocols.http.auto \
  --hidden-import=uvicorn.lifespan \
  --hidden-import=uvicorn.lifespan.on \
  --hidden-import=webview

echo ""
echo "Done. Run: ./dist/aais_desktop"
echo "Place .env next to the binary if you use cloud AI keys."
echo "Do NOT commit dist/ to GitHub."
