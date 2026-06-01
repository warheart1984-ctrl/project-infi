#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

METAL_ISO="${1:-${COGOS_DEBIAN_ISO:-${COGOS_METAL_ISO:-$DEBIAN_BASE_ISO}}}"
REPLAY_ISO="${2:-${COGOS_BOOT_REPLAY_ISO:-$METAL_ISO}}"
STRICT="${COGOS_PREFLIGHT_STRICT:-0}"

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: missing required tool: $1" >&2
    exit 2
  }
}

iso_has_file() {
  local iso="$1"
  local path="$2"
  local dir name
  dir="$(dirname "$path")"
  name="$(basename "$path")"
  xorriso -indev "$iso" -ls "${dir}/" 2>/dev/null | grep -F "'${name}'" >/dev/null
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

if [[ ! -f "$METAL_ISO" ]]; then
  echo "ERROR: baseline Debian live ISO not found: $METAL_ISO" >&2
  exit 3
fi

if [[ ! -f "$REPLAY_ISO" ]]; then
  echo "[preflight] WARN: boot replay ISO not found: $REPLAY_ISO" >&2
else
  check_boot_modes "$REPLAY_ISO" || true
fi

missing=()
for path in /boot/grub/install_start.cfg /boot/grub/install.cfg; do
  if iso_has_file "$METAL_ISO" "$path"; then
    echo "[preflight] Found $path in baseline ISO"
  else
    missing+=("$path")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "[preflight] WARN: baseline ISO missing Debian install GRUB assets: ${missing[*]}" >&2
  echo "[preflight] WARN: debian menu will omit Start installer / Advanced install options" >&2
  if [[ "$STRICT" == "1" ]]; then
    echo "[preflight] STRICT=1 -> failing build due to missing install assets" >&2
    exit 4
  fi
else
  echo "[preflight] Debian install GRUB assets present in baseline ISO"
fi

echo "[preflight] Debian installer preflight complete"
