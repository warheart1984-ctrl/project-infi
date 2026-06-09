#!/usr/bin/env bash
# Nightly variant build dry-run stub (cog-os; migrated from wolf-cog-os).
set -euo pipefail

if [[ "${1:-}" == "--dry-run" || "${1:-}" == "--build" ]]; then
  echo "forge-nightly-build dry-run: ok"
  exit 0
fi

echo "usage: $0 [--dry-run|--build]" >&2
exit 1
