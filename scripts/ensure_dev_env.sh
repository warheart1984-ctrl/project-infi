#!/usr/bin/env bash
# Create/refresh Python env with cori CLI for local/WSL CI scripts.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

# Windows-created .venv on /mnt/* has Scripts/ not bin/ — unusable from WSL.
use_wsl_venv=false
if [ -f .venv/Scripts/activate ] && [ ! -f .venv/bin/activate ]; then
  use_wsl_venv=true
elif [ -n "${WSL_DISTRO_NAME:-}" ] || grep -qi microsoft /proc/version 2>/dev/null; then
  if [ ! -f .venv/bin/activate ]; then
    use_wsl_venv=true
  fi
fi

if [ "$use_wsl_venv" = true ]; then
  VENV_DIR="${WSL_VENV:-$HOME/.venvs/project-infi}"
  if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    rm -rf "$VENV_DIR"
  fi
  if [ ! -d "$VENV_DIR" ]; then
    if python3 -m venv "$VENV_DIR" 2>/dev/null; then
      echo "Created WSL venv: $VENV_DIR"
    else
      echo "python3-venv unavailable — using pip --user (install: sudo apt install python3-venv)"
      VENV_DIR=""
    fi
  fi
else
  VENV_DIR="$ROOT/.venv"
  if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
  fi
fi

pip_install() {
  if [ -n "${VENV_DIR:-}" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck source=/dev/null
    . "$VENV_DIR/bin/activate"
    if command -v cori >/dev/null 2>&1; then
      return 0
    fi
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    pip install -q -e .
  else
    if command -v cori >/dev/null 2>&1; then
      return 0
    fi
    python3 -m pip install --user -q --upgrade pip --break-system-packages
    python3 -m pip install --user -q -r requirements.txt --break-system-packages
    python3 -m pip install --user -q -e . --break-system-packages
  fi
}

pip_install

command -v cori >/dev/null
echo "Python env ready: $(python3 --version), cori=$(command -v cori)"
