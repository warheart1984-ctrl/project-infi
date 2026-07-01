#!/usr/bin/env bash
# Quickstart Nova Desktop + governed Node backend from a fresh GitHub download.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP="${ROOT}/desktop"
NO_DESKTOP=false
NO_START=false
SKIP_TESTS=false

for arg in "$@"; do
  case "$arg" in
    --no-desktop) NO_DESKTOP=true ;;
    --no-start) NO_START=true ;;
    --skip-tests) SKIP_TESTS=true ;;
    --help|-h)
      echo "Usage: ./quickstart.sh [--no-desktop] [--no-start] [--skip-tests]"
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

log() { printf '[quickstart] %s\n' "$*"; }
ok() { printf '[OK] %s\n' "$*"; }

cd "$ROOT"
log "Setting up governed Node backend from $ROOT"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv "$ROOT/.venv"
  elif command -v python >/dev/null 2>&1; then
    python -m venv "$ROOT/.venv"
  else
    echo "Python 3.10+ is required. Install Python 3.12 and rerun quickstart.sh." >&2
    exit 1
  fi
fi

PY="$ROOT/.venv/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -e ".[dev]"
ok "Python backend installed"

if [[ -d "$DESKTOP" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Node.js 20+ and npm are required for Nova Desktop." >&2
    exit 1
  fi
  (cd "$DESKTOP" && npm install && { [[ "$SKIP_TESTS" == true ]] || npm test; })
  ok "Desktop dependencies installed"
fi

if [[ "$SKIP_TESTS" != true ]]; then
  "$PY" -m pytest tests -q
  "$ROOT/setup/verify.sh"
fi

if [[ "$NO_START" == true ]]; then
  cat <<EOF

Setup complete. Start manually:
  .venv/bin/python -m nova.api
  cd desktop && npm start
EOF
  exit 0
fi

log "Starting governed Node backend: python -m nova.api"
"$PY" -m nova.api &
NODE_PID=$!
sleep 3
ok "Node backend started as PID $NODE_PID"
echo "Node status: http://127.0.0.1:8080/node/status"

if [[ "$NO_DESKTOP" != true && -d "$DESKTOP" ]]; then
  log "Starting Nova Desktop"
  (cd "$DESKTOP" && npm start)
fi
