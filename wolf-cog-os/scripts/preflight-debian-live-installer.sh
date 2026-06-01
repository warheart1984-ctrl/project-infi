#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

BASE_ISO="${1:-${COGOS_DEBIAN_ISO:-$DEBIAN_BASE_ISO}}"
REPLAY_ISO="${2:-${COGOS_BOOT_REPLAY_ISO:-$BASE_ISO}}"

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: missing required tool: $1" >&2
    exit 2
  }
}

check_boot_modes() {
  local iso="$1"
  local report
  local bios=0
  local uefi=0

  report="$(xorriso -indev "$iso" -report_el_torito plain 2>/dev/null || true)"
  if [[ "$report" == *"Platform Id   : 0x00"* || "$report" == *" Pltf  BIOS "* || "$report" == *"  BIOS  "* ]]; then
    bios=1
  fi
  if [[ "$report" == *"Platform Id   : 0xef"* || "$report" == *" Pltf  UEFI "* || "$report" == *"  UEFI  "* ]]; then
    uefi=1
  fi

  if [[ "$bios" == "1" && "$uefi" == "1" ]]; then
    echo "[preflight] Boot replay ISO has BIOS+UEFI El Torito entries"
    return 0
  fi

  echo "[preflight] WARN: replay ISO may not have full BIOS+UEFI spread (bios=$bios uefi=$uefi)" >&2
  return 1
}

require_tool xorriso
require_tool unsquashfs
require_tool mksquashfs

if [[ ! -f "$BASE_ISO" ]]; then
  echo "ERROR: Debian live ISO not found: $BASE_ISO" >&2
  exit 3
fi

if [[ ! -f "$REPLAY_ISO" ]]; then
  echo "[preflight] WARN: boot replay ISO not found: $REPLAY_ISO" >&2
else
  check_boot_modes "$REPLAY_ISO" || true
fi

echo "[preflight] Debian live installer preflight complete"
