#!/usr/bin/env bash
# Pack ISO only from an existing workdir (skip extract/unsquashfs/squashfs).
# Use when mksquashfs already completed but xorriso pack failed or was interrupted.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=build_iso.sh
source "$SCRIPT_DIR/build_iso.sh"

WORK="${COGOS_WORK:-${HOME}/.cogos-universal-installer-work}"
ISO="${1:-${HOME}/debian-live-13.5.0-amd64-cinnamon.iso}"
OUT="$(wolf_iso_out)"
REPLAY_ISO="${COGOS_BOOT_REPLAY_ISO:-$ISO}"

if [[ ! -f "$WORK/iso/live/filesystem.squashfs" ]]; then
  echo "ERROR: missing squashfs: $WORK/iso/live/filesystem.squashfs" >&2
  echo "Run full build first." >&2
  exit 3
fi

if [[ ! -f "$ISO" ]]; then
  echo "ERROR: replay ISO not found: $ISO" >&2
  exit 3
fi

echo "=== Pack Wolf CoG OS ISO (squashfs reuse) ==="
echo "Work:   $WORK"
echo "Replay: $REPLAY_ISO"
echo "Output: $OUT"
ls -lh "$WORK/iso/live/filesystem.squashfs"

echo "[9/9] Rebuild ISO (replay Debian live boot images from source ISO)"
build_iso_from_workdir "$WORK" "$REPLAY_ISO" "$OUT"

COGOS_OUT_FINAL="${COGOS_OUT_FINAL:-/mnt/e/project-infi/Wolf-CoG-OS-full.iso}"
if [[ "$OUT" != "$COGOS_OUT_FINAL" && -f "$OUT" ]]; then
  cp -f "$OUT" "${OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $OUT" >&2
fi

echo "=== ISO pack complete ==="
ls -lh "$OUT" "${OUT}.sha256" 2>/dev/null || true
