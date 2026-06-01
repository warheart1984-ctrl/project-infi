#!/usr/bin/env bash
# Local promotion readiness dry-run for Forge-tagged RC artifacts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FIXTURES="$REPO_ROOT/wolf-cog-os/scripts/test/fixtures/promotion-forge-rc"
ARTIFACTS_DIR=""
SOURCE_RUN_ID="424242"
EXPECTED_PROFILE="forge-selfhosted"
SKIP_VERIFY=0

usage() {
  cat <<USAGE
Usage:
  bash wolf-cog-os/scripts/test/promotion-dry-run.sh [--fixtures] [--artifacts-dir PATH] [--source-run-id ID]

Runs promotion source validation and emits promotion-dry-run-report.json.
Default uses bundled Forge RC fixture artifacts for local proof.
USAGE
}

while (($# > 0)); do
  case "$1" in
    --fixtures)
      ARTIFACTS_DIR="$FIXTURES"
      shift
      ;;
    --artifacts-dir)
      ARTIFACTS_DIR="$2"
      shift 2
      ;;
    --source-run-id)
      SOURCE_RUN_ID="$2"
      shift 2
      ;;
    --expected-profile)
      EXPECTED_PROFILE="$2"
      shift 2
      ;;
    --skip-verify)
      SKIP_VERIFY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$ARTIFACTS_DIR" ]]; then
  ARTIFACTS_DIR="$FIXTURES"
fi

if [[ ! -d "$ARTIFACTS_DIR" ]]; then
  echo "ERROR: artifacts dir not found: $ARTIFACTS_DIR" >&2
  exit 3
fi

cd "$REPO_ROOT"
mkdir -p ci-artifacts

python3 .github/scripts/validate-promotion-source.py \
  --artifacts-dir "$ARTIFACTS_DIR" \
  --source-run-id "$SOURCE_RUN_ID" \
  --expected-profile-id "$EXPECTED_PROFILE" \
  --required-scenarios "1,3,4,6" \
  --output "ci-artifacts/promotion-source-validation.json"

if [[ "$SKIP_VERIFY" -eq 0 && -f "$ARTIFACTS_DIR/artifact-manifest.json" ]]; then
  MINISIGN_PUBLIC_KEY="${MINISIGN_PUBLIC_KEY:-}" make verify-artifacts ARTIFACT_DIR="$ARTIFACTS_DIR" || {
    echo "WARN: signature verify failed or keys missing; continuing dry-run evidence capture" >&2
  }
fi

python3 .github/scripts/emit-promotion-dry-run-report.py \
  --artifacts-dir "$ARTIFACTS_DIR" \
  --source-run-id "$SOURCE_RUN_ID" \
  --expected-profile-id "$EXPECTED_PROFILE" \
  --required-scenarios "1,3,4,6" \
  --promotion-validation "ci-artifacts/promotion-source-validation.json" \
  --output "ci-artifacts/promotion-dry-run-report.json"

echo "promotion dry-run complete"
