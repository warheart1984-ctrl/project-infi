#!/usr/bin/env bash
# Build terminal-only AAIS desktop executable (Linux).
# Output: dist/aais_terminal (not committed to git)

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Installing desktop build dependencies..."
python -m pip install -q -e ".[dev,desktop]"

echo "Preparing frontend bundle..."
python -m aais prepare --data-dir "$ROOT/.runtime/aais-data"

echo "Running PyInstaller (terminal)..."
python -m PyInstaller --onefile --name aais_terminal --clean run_aais.py \
  --hidden-import=uvicorn \
  --hidden-import=uvicorn.logging \
  --hidden-import=uvicorn.loops \
  --hidden-import=uvicorn.loops.auto \
  --hidden-import=uvicorn.protocols \
  --hidden-import=uvicorn.protocols.http \
  --hidden-import=uvicorn.protocols.http.auto \
  --hidden-import=uvicorn.lifespan \
  --hidden-import=uvicorn.lifespan.on

echo ""
echo "Done. Run: ./dist/aais_terminal"
echo "Place .env next to the binary if you use cloud AI keys."
echo "Do NOT commit dist/ to GitHub."
