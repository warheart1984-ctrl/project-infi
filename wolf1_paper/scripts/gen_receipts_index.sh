#!/usr/bin/env bash
# Aggregate governance/receipts/*.json → governance/receipts-index.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REC_DIR="governance/receipts"
INDEX="governance/receipts-index.json"
mkdir -p "$REC_DIR"

if command -v jq >/dev/null 2>&1; then
  shopt -s nullglob
  files=("$REC_DIR"/*.json)
  filtered=()
  for f in "${files[@]}"; do
    base=$(basename "$f")
    [ "$base" = "receipts-index.json" ] && continue
    filtered+=("$f")
  done
  if [ ${#filtered[@]} -eq 0 ]; then
    echo '[]' > "$INDEX"
  else
    jq -s 'sort_by(.timestamp) | reverse' "${filtered[@]}" > "$INDEX"
  fi
else
  node scripts/gen_receipts_index.mjs
  exit $?
fi

echo "[RECEIPTS-INDEX] Wrote $INDEX"
