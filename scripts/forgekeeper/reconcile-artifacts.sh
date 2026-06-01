#!/usr/bin/env bash
# Refresh governance artifact linkage (report -> snapshot -> snapshot-index).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}"

PLAN_ID="${1:-bf-reconcile}"
FIXED_TS="${2:-2026-05-28T12:00:00Z}"

py -3.12 -m forge.forgekeeper --mode reconcile-artifacts \
  --plan-id "${PLAN_ID}" --scope . --fixed-timestamp "${FIXED_TS}" \
  --proof-dir docs/proof/bumblebee-forge \
  --plan-artifact docs/proof/bumblebee-forge/stage2_attested_plan.json \
  --ledger-path .runtime/forgekeeper/decision_ledger.jsonl \
  --report-path docs/proof/bumblebee-forge/forgekeeper_report.json \
  --snapshot-path docs/proof/bumblebee-forge/forgekeeper_snapshot.json \
  --snapshot-index-path docs/proof/bumblebee-forge/forgekeeper_snapshot_index.jsonl
