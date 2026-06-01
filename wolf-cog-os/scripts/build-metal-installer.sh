#!/usr/bin/env bash
# Wolf CoG OS — Metal-baseline installer ISO
#
# Reverse-engineered from Wolf-CoG-OS-metal-fixed.iso (proven live boot).
# Live session: systemd PID1, minimal GRUB, nomodeset.
# Disk install: cogos-install (rsync → PID1 chain → initramfs → grub).
#
# Usage:
#   bash wolf-cog-os/scripts/build-metal-installer.sh [Wolf-CoG-OS-metal-fixed.iso]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

TAG="${COGOS_TAG:-metal-installer-1.0}"
BUILD_DATE="${COGOS_BUILD_DATE:-$(date -u +%Y-%m-%d)}"
export COGOS_TAG="$TAG"
export COGOS_BUILD_DATE="$BUILD_DATE"
export COGOS_ENABLE_PID1=0
export COGOS_METAL_INSTALL=1
export COGOS_STEALTH_INSTALL=0
export COGOS_SURPRISE_INSTALL=0
export COGOS_GRUB_MERGE=1
export COGOS_BOOT_PROFILE=metal
export COGOS_LIVE_FINDISO=0
export COGOS_SQUASHFS_COMP="${COGOS_SQUASHFS_COMP:-xz}"
export COGOS_WORK="${COGOS_METAL_WORK:-${HOME}/.cogos-metal-installer-work}"

METAL_ISO="${1:-${COGOS_METAL_ISO:-${HOME}/Wolf-CoG-OS-metal-fixed.iso}}"
if [[ ! -f "$METAL_ISO" && -f "/mnt/e/project-infi/Wolf-CoG-OS-metal-fixed.iso" ]]; then
  METAL_ISO="/mnt/e/project-infi/Wolf-CoG-OS-metal-fixed.iso"
fi

if [[ ! -f "$METAL_ISO" ]]; then
  echo "ERROR: metal baseline ISO not found: $METAL_ISO" >&2
  echo "Run: bash wolf-cog-os/scripts/extract-metal-iso.sh" >&2
  exit 3
fi

# Metal-fixed.iso has overlapping hybrid GPT; replay boot from stock Debian live instead.
if [[ -z "${COGOS_BOOT_REPLAY_ISO:-}" ]]; then
  if [[ -f "${HOME}/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
    export COGOS_BOOT_REPLAY_ISO="${HOME}/debian-live-13.5.0-amd64-cinnamon.iso"
  elif [[ -f "/mnt/e/project-infi/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
    export COGOS_BOOT_REPLAY_ISO="/mnt/e/project-infi/debian-live-13.5.0-amd64-cinnamon.iso"
  fi
fi

COGOS_OUT_FINAL="${COGOS_OUT:-$REPO_ROOT/Wolf-CoG-OS-metal-installer.iso}"
if [[ "$COGOS_OUT_FINAL" == /mnt/* ]]; then
  export COGOS_OUT="${HOME}/Wolf-CoG-OS-metal-installer.iso"
else
  export COGOS_OUT="$COGOS_OUT_FINAL"
fi

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK on Windows mount (9p) breaks unsquashfs symlinks." >&2
  exit 4
fi

if [[ -z "${COGOS_PAYLOAD:-}" && -f "${HOME}/.cogos-payload-cache/opt/cogos/config/release_manifest.json" ]]; then
  export COGOS_PAYLOAD="${HOME}/.cogos-payload-cache"
fi
if [[ -f "$WOLF_PAYLOAD/opt/cogos/bin/cognitive_init" ]]; then
  export COGOS_PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
fi

echo "=== Wolf CoG OS Metal Installer ISO ==="
echo "Tag:        $COGOS_TAG"
echo "Substrate:  $METAL_ISO"
echo "Live boot:  systemd PID1 (metal baseline)"
echo "Install:    cogos-install apply (terminal)"
echo "Output:     $COGOS_OUT"
echo "Payload:    ${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
echo "Boot replay:${COGOS_BOOT_REPLAY_ISO:-same as substrate}"

bash "$SCRIPT_DIR/diagnose-metal-iso.sh" 2>/dev/null | tail -20 || true

bash "$SCRIPT_DIR/build.sh" "$METAL_ISO"

if [[ "$COGOS_OUT" != "$COGOS_OUT_FINAL" ]]; then
  cp -f "$COGOS_OUT" "${COGOS_OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $COGOS_OUT" >&2
fi

echo ""
echo "=== Metal installer ISO complete ==="
echo "Flash: Ventoy or Rufus DD"
echo "Boot:  Wolf CoG OS — Live (metal baseline)"
echo "Install from live terminal:"
echo "  sudo cogos-install plan --target /dev/nvme0n1"
echo "  sudo cogos-install apply --target /dev/nvme0n1 --yes --confirm-erase nvme0n1"
echo "SHA:   ${COGOS_OUT}.sha256"
ls -lh "$COGOS_OUT" "${COGOS_OUT}.sha256" 2>/dev/null || true
