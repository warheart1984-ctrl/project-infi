#!/usr/bin/env bash
# Finish surprise ISO from existing workdir (skip stages 1-7).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

WORK="${COGOS_SURPRISE_WORK:-${HOME}/.cogos-surprise-work}"
REPLAY_ISO="${1:-${COGOS_DEBIAN_ISO:-${HOME}/debian-live-13.5.0-amd64-cinnamon.iso}}"
export COGOS_TAG="${COGOS_TAG:-daily-driver-1.6-surprise}"
export COGOS_OUT="${COGOS_OUT:-${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso}"
OUT="$(wolf_iso_out)"

if [[ ! -d "$WORK/iso/live" ]]; then
  echo "ERROR: workdir missing: $WORK" >&2
  exit 1
fi
if [[ ! -f "$WORK/iso/live/filesystem.squashfs" ]]; then
  echo "ERROR: squashfs missing in $WORK/iso/live/" >&2
  exit 1
fi
if [[ ! -f "$REPLAY_ISO" ]]; then
  echo "ERROR: source ISO not found: $REPLAY_ISO" >&2
  exit 1
fi

# shellcheck source=build_iso.sh
source "$SCRIPT_DIR/build_iso.sh"

echo "[8/8] Rebuild ISO from $WORK"
build_iso_from_workdir "$WORK" "$REPLAY_ISO" "$OUT"

COGOS_OUT_FINAL="${COGOS_OUT_FINAL:-/mnt/e/project-infi/Wolf-CoG-OS-daily-driver-surprise.iso}"
if [[ "$OUT" != "$COGOS_OUT_FINAL" && "$COGOS_OUT_FINAL" == /mnt/* ]]; then
  cp -f "$OUT" "${OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $OUT" >&2
fi

echo "=== Surprise ISO complete ==="
ls -lh "$OUT" "${OUT}.sha256" "$COGOS_OUT_FINAL" 2>/dev/null || true
