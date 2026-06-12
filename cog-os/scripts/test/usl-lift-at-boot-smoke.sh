#!/usr/bin/env bash
# Static proof that guest USL lift-at-boot wiring is present (no forge rebake required).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COG_OS_DIR="$REPO_ROOT/cog-os"

fail=0
check_file_contains() {
  local file="$1"
  local needle="$2"
  if [[ ! -f "$file" ]]; then
    echo "FAIL missing file: $file" >&2
    fail=1
    return
  fi
  if ! grep -q "$needle" "$file"; then
    echo "FAIL $file missing: $needle" >&2
    fail=1
    return
  fi
  echo "OK $file contains $needle"
}

START_USL="$COG_OS_DIR/payload/opt/cogos/bin/start-usl"
FIRSTBOOT="$COG_OS_DIR/host/scripts/lib/cogos-firstboot-invariants.sh"

check_file_contains "$START_USL" "USL_LIFT_ELF"
check_file_contains "$START_USL" "USL_GOVERNANCE_ADMISSION"
check_file_contains "$START_USL" "governance_decode_bundle.json"
check_file_contains "$FIRSTBOOT" "USL_LIFT_ELF"

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "usl-lift-at-boot-smoke: PASS"
