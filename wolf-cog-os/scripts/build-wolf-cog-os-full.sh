#!/usr/bin/env bash
# Canonical Wolf CoG OS regular edition (full runtime) ISO build entry point.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/build-universal-installer.sh" "$@"
