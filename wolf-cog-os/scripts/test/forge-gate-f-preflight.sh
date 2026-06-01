#!/usr/bin/env bash
# Gate F readiness preflight — validates local gates and optional RC artifact bundle.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

ARTIFACTS="${1:-ci-artifacts}"
SOURCE_RUN_ID="${2:-${GITHUB_RUN_ID:-424242}}"
PROFILE="${3:-forge-selfhosted}"
STRICT=0
if [[ "${4:-}" == "--strict" ]]; then
  STRICT=1
fi

echo "=== Gate F preflight ==="
echo "artifacts: $ARTIFACTS"
echo "source_run_id: $SOURCE_RUN_ID"
echo "strict: $STRICT"

make forge-shippable-gate

if [[ -f "$ARTIFACTS/forge-lineage.json" ]]; then
  python3 wolf-cog-os/scripts/validate-forge-lineage.py \
    --lineage "$ARTIFACTS/forge-lineage.json" \
    --mode fail
else
  echo "WARN: $ARTIFACTS/forge-lineage.json missing (non-strict preflight continues)"
  if [[ "$STRICT" -eq 1 ]]; then
    exit 1
  fi
fi

if [[ "$STRICT" -eq 1 ]]; then
  python3 .github/scripts/check-forge-shippable-gate.py \
    --artifacts-dir "$ARTIFACTS" \
    --source-run-id "$SOURCE_RUN_ID" \
    --expected-profile-id "$PROFILE" \
    --mode fail
fi

echo "gate F preflight: pass"
