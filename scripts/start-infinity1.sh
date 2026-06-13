#!/usr/bin/env bash
# Infinity 1 — install dependencies and start AAIS (default preset: real AI + Nova companion).
# Usage: ./scripts/start-infinity1.sh
#        ./scripts/start-infinity1.sh --replace-existing
#        ./scripts/start-infinity1.sh --preset laptop
#        ./scripts/start-infinity1.sh --preset mock

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${AAIS_PORT:-8000}"
DATA_DIR="${AAIS_DATA_DIR:-./.runtime/aais-data}"
PRESET="${AAIS_PRESET:-default}"
REPLACE_EXISTING=0
SKIP_INSTALL=0

for arg in "$@"; do
  case "$arg" in
    --replace-existing) REPLACE_EXISTING=1 ;;
    --skip-install) SKIP_INSTALL=1 ;;
    --preset=*) PRESET="${arg#*=}" ;;
    --help|-h)
      echo "Usage: $0 [--replace-existing] [--skip-install] [--preset=default|laptop|mock]"
      exit 0
      ;;
  esac
done

case "$PRESET" in
  default|laptop|mock) ;;
  *)
    echo "Invalid preset: $PRESET (use default, laptop, or mock)" >&2
    exit 1
    ;;
esac

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null && { echo python3; return; }
  fi
  if command -v python >/dev/null 2>&1; then
    python -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null && { echo python; return; }
  fi
  echo "Python 3.10+ required." >&2
  exit 1
}

echo "=== Project Infinity 1 — AAIS bootstrap ==="
echo "Repo: $ROOT"

PY="$(find_python)"
echo "Python: $PY"

VENV="$ROOT/.venv"
if [[ "$SKIP_INSTALL" -eq 0 ]]; then
  if [[ ! -x "$VENV/bin/python" ]]; then
    echo "Creating virtual environment..."
    "$PY" -m venv "$VENV"
  fi
  if ! "$VENV/bin/python" -m pip --version >/dev/null 2>&1; then
    echo "Bootstrapping pip in .venv (ensurepip)..."
    "$VENV/bin/python" -m ensurepip --upgrade || {
      echo "Recreating broken virtual environment..."
      rm -rf "$VENV"
      "$PY" -m venv "$VENV"
      "$VENV/bin/python" -m ensurepip --upgrade
    }
  fi
  echo "Installing AAIS package and dependencies (editable)..."
  "$VENV/bin/python" -m pip install --upgrade pip wheel setuptools
  "$VENV/bin/python" -m pip install -e ".[dev]"
fi

RUN_PY="$VENV/bin/python"
if [[ ! -x "$RUN_PY" ]]; then
  echo "Missing .venv — run without --skip-install" >&2
  exit 1
fi

if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example (set provider keys in .env for frontier models)"
fi

echo "Preparing runtime data..."
"$RUN_PY" -m aais prepare --data-dir "$DATA_DIR"
"$RUN_PY" -m aais doctor --data-dir "$DATA_DIR"

if command -v lsof >/dev/null 2>&1; then
  PID="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null | head -1 || true)"
  if [[ -n "$PID" ]]; then
    if [[ "$REPLACE_EXISTING" -eq 1 ]]; then
      echo "Stopping process on port $PORT (PID $PID)..."
      kill "$PID" 2>/dev/null || true
      sleep 2
    else
      echo "Port $PORT is in use (PID $PID)."
      echo "  Option A: $0 --replace-existing"
      echo "  Option B: curl http://127.0.0.1:$PORT/health"
      exit 1
    fi
  fi
fi

echo ""
echo "Starting AAIS (preset=$PRESET, no browser)..."
echo "  Health:   http://127.0.0.1:$PORT/health"
echo "  App:      http://127.0.0.1:$PORT/app"
echo "  Jarvis:   http://127.0.0.1:$PORT/app/jarvis"
echo "  Operator: http://127.0.0.1:$PORT/operator"
echo ""
echo "Press Ctrl+C to stop."
echo ""

exec "$RUN_PY" -m aais start --data-dir "$DATA_DIR" --preset "$PRESET" --no-browser --port "$PORT"
