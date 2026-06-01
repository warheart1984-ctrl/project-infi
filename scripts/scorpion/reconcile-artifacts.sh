#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
CASE_ID="${SCORPION_CASE_ID:-sc-reconcile}"
TRACE="${SCORPION_TRACE:-scorpion/fixtures/traces/fd_leak.ndjson}"
FIXED_TS="${SCORPION_FIXED_TS:-2026-05-29T12:00:00Z}"
py -3.12 -m scorpion.scorpion --mode reconcile-artifacts \
  --case-id "$CASE_ID" \
  --trace-path "$TRACE" \
  --fixed-timestamp "$FIXED_TS" \
  --proof-dir docs/proof/scorpion \
  --ledger-path .runtime/scorpion/anomaly_ledger.jsonl
