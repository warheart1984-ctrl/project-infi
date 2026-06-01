#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
CASE_ID="${SCORPION_CASE_ID:-sc-weekly}"
TRACE="${SCORPION_TRACE:-scorpion/fixtures/traces/fd_leak.ndjson}"
py -3.12 -m scorpion.scorpion --mode scan --case-id "$CASE_ID" --trace-path "$TRACE"
py -3.12 -m scorpion.scorpion --mode verify --case-id "$CASE_ID" --write-verify-report docs/proof/scorpion/scorpion_verify_report.json
py -3.12 -m scorpion.scorpion --mode chaos-check --case-id "$CASE_ID"
py -3.12 -m scorpion.scorpion --mode drift-window-query --case-id "$CASE_ID" --window 5
