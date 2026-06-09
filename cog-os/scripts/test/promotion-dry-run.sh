#!/usr/bin/env bash
# Local promotion dry-run using bundled RC fixture (no GitHub artifact download).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FIXTURE="${COG_FIXTURE_DIR:-$REPO_ROOT/cog-os/scripts/test/fixtures/promotion-forge-rc}"
SOURCE_RUN_ID="${COG_SOURCE_RUN_ID:-424242}"
PROFILE_ID="${COG_EXPECTED_PROFILE:-forge-selfhosted}"
SCENARIOS="${COG_REQUIRED_SCENARIOS:-1,3,4,6}"
OUTPUT_DIR="${COG_OUTPUT_DIR:-$REPO_ROOT/ci-artifacts}"
SKIP_VERIFY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --fixture) FIXTURE="$2"; shift 2 ;;
    --source-run-id) SOURCE_RUN_ID="$2"; shift 2 ;;
    --expected-profile-id) PROFILE_ID="$2"; shift 2 ;;
    --required-scenarios) SCENARIOS="$2"; shift 2 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    --skip-verify) SKIP_VERIFY=1; shift ;;
    -h|--help)
      echo "usage: $0 [--skip-verify] [--fixture PATH] [--source-run-id ID]"
      exit 0
      ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON="python"
fi

[[ -d "$FIXTURE" ]] || { echo "fixture missing: $FIXTURE" >&2; exit 1; }
mkdir -p "$OUTPUT_DIR"

VALIDATION_JSON="$OUTPUT_DIR/promotion-source-validation.json"
REPORT_JSON="$OUTPUT_DIR/promotion-dry-run-report.json"

"$PYTHON" "$REPO_ROOT/.github/scripts/validate-promotion-source.py" \
  --artifacts-dir "$FIXTURE" \
  --source-run-id "$SOURCE_RUN_ID" \
  --expected-profile-id "$PROFILE_ID" \
  --required-scenarios "$SCENARIOS" \
  --output "$VALIDATION_JSON"

if [[ "$SKIP_VERIFY" == "0" ]]; then
  if ! compgen -G "$FIXTURE/*.minisig" >/dev/null; then
    echo "WARN: no .minisig files in fixture (use --skip-verify to ignore locally)" >&2
  fi
fi

"$PYTHON" "$REPO_ROOT/.github/scripts/emit-promotion-dry-run-report.py" \
  --artifacts-dir "$FIXTURE" \
  --source-run-id "$SOURCE_RUN_ID" \
  --expected-profile-id "$PROFILE_ID" \
  --required-scenarios "$SCENARIOS" \
  --promotion-validation "$VALIDATION_JSON" \
  --output "$REPORT_JSON"

echo "promotion dry-run PASS fixture=$FIXTURE report=$REPORT_JSON"
