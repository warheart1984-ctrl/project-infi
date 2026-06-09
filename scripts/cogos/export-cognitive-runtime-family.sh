#!/usr/bin/env bash
# Export cognitive runtime family JSON from repo authority into Nova NorthStar CoG OS payload.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TARGET="${1:-$REPO_ROOT/cog-os/payload/opt/cogos/config/cognitive_runtime_family.json}"

PYTHONPATH="$REPO_ROOT" python3 <<PY
from pathlib import Path
from src.cog_runtime import export_family_json

target = Path(r"$TARGET")
export_family_json(target)
print(target)
PY
