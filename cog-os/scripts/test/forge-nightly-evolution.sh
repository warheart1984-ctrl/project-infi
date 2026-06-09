#!/usr/bin/env bash
# Nightly evolution dry-run (cog-os; migrated from wolf-cog-os).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "forge-nightly-evolution dry-run: ok"
  exit 0
fi

bash cog-os/forge/scripts/lib/profile-loader.sh --profile metal --print >/dev/null
bash cog-os/scripts/test/qemu-smoke.sh --contract --profile metal
echo "forge-nightly-evolution: ok"
