#!/usr/bin/env bash
# Post-build boot trace ingest for Scorpion (INACTIVE by default).
set -euo pipefail
if [[ "${SCORPION_WOLF_INGEST:-inactive}" != "active" ]]; then
  echo "[scorpion-ingest] inactive (set SCORPION_WOLF_INGEST=active to enable)"
  exit 0
fi
TRACE_PATH="${1:-}"
if [[ -z "$TRACE_PATH" || ! -f "$TRACE_PATH" ]]; then
  echo "[scorpion-ingest] trace path required" >&2
  exit 1
fi
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
py -3.12 -m scorpion.scorpion --mode ingest --case-id "wolf-boot" --trace-path "$TRACE_PATH" --scope wolf-cog-os
