#!/usr/bin/env bash
# INV-1 single-machine Wolf rehydration smoke gate.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STORE_ROOT="${1:-$REPO_ROOT/.runtime/wolf_rehydration_smoke}"

cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo "[wolf-rehydration] running harness against $STORE_ROOT"
python -m src.cogos_runtime_bridge --verify-rehydration "$STORE_ROOT"
python -m pytest tests/test_wolf_rehydration_harness.py -q
echo "[wolf-rehydration] OK"
