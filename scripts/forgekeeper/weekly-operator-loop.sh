#!/usr/bin/env bash
# Weekly operator loop (BF-DOC-001). Non-destructive; dry-run only.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}"
PLAN_ID="${1:-bf-weekly}"
FIXED_TS="${2:-2026-05-28T12:00:00Z}"
VERIFY_PATH="docs/proof/bumblebee-forge/forgekeeper_verify_report.json"

echo "=== Step B: reconcile artifacts ==="
py -3.12 -m forge.forgekeeper --mode reconcile-artifacts --plan-id "${PLAN_ID}" --scope . \
  --fixed-timestamp "${FIXED_TS}" --proof-dir docs/proof/bumblebee-forge \
  --plan-artifact docs/proof/bumblebee-forge/stage2_attested_plan.json

echo "=== Step C: verify export ==="
py -3.12 -m forge.forgekeeper --mode verify --plan-id "${PLAN_ID}" --scope . \
  --fixed-timestamp "${FIXED_TS}" --write-report "${VERIFY_PATH}"

echo "=== Step D: seam checks ==="
py -3.12 -m forge.forgekeeper --mode trace-query --plan-id "${PLAN_ID}" --scope .
py -3.12 -m forge.forgekeeper --mode reconcile-query --plan-id "${PLAN_ID}" --scope .
py -3.12 -m forge.forgekeeper --mode drift-window-query --plan-id "${PLAN_ID}" --scope .

echo "=== Step E: chaos-check ==="
py -3.12 -m forge.forgekeeper --mode chaos-check --plan-id "${PLAN_ID}" --scope .

echo "=== Step F: bundle-export ==="
py -3.12 -m forge.forgekeeper --mode bundle-export --plan-id "${PLAN_ID}" --scope . \
  --fixed-timestamp "${FIXED_TS}" --verify-report-path "${VERIFY_PATH}" \
  --write-bundle-export docs/proof/bumblebee-forge/forgekeeper_bundle_manifest.json

echo "=== Done (review output; update STAGE1_PROOF_BUNDLE.md) ==="
