#!/usr/bin/env bash
# Quick smoke: Ubuntu ISO → replay adapter → squashfs extract
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

ISO="${1:-ubuntu-26.04-desktop-amd64.iso}"
if [[ ! -f "$ISO" ]]; then
  echo "ERROR: ISO not found: $ISO" >&2
  exit 3
fi

export COGOS_SUBSTRATE_ISO="$ISO"
export COGOS_SUBSTRATE_ID="${COGOS_SUBSTRATE_ID:-ubuntu-live}"
export COGOS_REPLAY_ADAPTER="${COGOS_REPLAY_ADAPTER:-ubuntu-live-layout}"

WORK="${COGOS_WORK:-$HOME/.forge-ubuntu-smoke}"
rm -rf "$WORK"
mkdir -p "$WORK/iso" "$WORK/rootfs"

echo "=== Ubuntu substrate smoke ==="
echo "ISO: $ISO"
echo "substrate_id: $COGOS_SUBSTRATE_ID"

python3 wolf-cog-os/scripts/validate-substrate.py \
  --iso "$ISO" \
  --substrate-id "$COGOS_SUBSTRATE_ID" \
  --mode fail \
  --output ci-artifacts/ubuntu-substrate-smoke.json

echo "[1/3] Resolve squashfs inside ISO..."
SFS_ISO_PATH=""
for candidate in \
  /casper/minimal.standard.live.squashfs \
  /casper/filesystem.squashfs \
  /casper/minimal.standard.squashfs; do
  if xorriso -indev "$ISO" -find "$candidate" 2>/dev/null | grep -q .; then
    SFS_ISO_PATH="$candidate"
    break
  fi
done
if [[ -z "$SFS_ISO_PATH" ]]; then
  SFS_ISO_PATH="$(xorriso -indev "$ISO" -find /casper -name '*live*.squashfs' 2>/dev/null | head -n 1 | tr -d "'")"
fi
if [[ -z "$SFS_ISO_PATH" ]]; then
  echo "FAIL: could not locate Ubuntu casper squashfs in ISO" >&2
  exit 4
fi
echo "squashfs path in ISO: $SFS_ISO_PATH"
mkdir -p "$WORK/iso/casper"
SFS_LOCAL="$WORK/iso${SFS_ISO_PATH}"
mkdir -p "$(dirname "$SFS_LOCAL")"
echo "[2/3] Extract squashfs only (not full ISO tree)..."
xorriso -osirrox on -indev "$ISO" -extract "$SFS_ISO_PATH" "$SFS_LOCAL" >/dev/null
export SFS_SOURCE="$SFS_LOCAL"
export SFS_NAME="$(basename "$SFS_LOCAL")"
export COGOS_REPLAY_ADAPTER=ubuntu-live-layout

SCRIPT_DIR="$ROOT_DIR/wolf-cog-os/scripts"
# shellcheck source=../lib/replay-adapters.sh
source "$SCRIPT_DIR/lib/replay-adapters.sh"
echo "replay_adapter=${COGOS_REPLAY_ADAPTER}"
echo "SFS_SOURCE=${SFS_SOURCE}"

echo "[3/3] unsquashfs extract..."
if [[ "$(id -u)" -eq 0 ]]; then
  replay_extract_rootfs "$WORK/iso" "$WORK/rootfs"
else
  sudo bash -c "export COGOS_XATTRS=0; source '$SCRIPT_DIR/lib/replay-adapters/ubuntu-live-layout.sh'; SFS_SOURCE='$SFS_SOURCE'; adapter_extract_rootfs '$WORK/iso' '$WORK/rootfs'"
fi
if [[ ! -f "$WORK/rootfs/etc/os-release" ]]; then
  echo "FAIL: /etc/os-release missing after extract" >&2
  exit 5
fi

echo "PASS: Ubuntu squashfs extracted"
head -5 "$WORK/rootfs/etc/os-release"
echo "workdir=$WORK"
