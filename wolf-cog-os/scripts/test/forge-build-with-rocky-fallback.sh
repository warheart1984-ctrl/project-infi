#!/usr/bin/env bash
# Build Forge ISO: native rootfs paths, Ubuntu substrate first, Rocky fallback on ISO failure.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=../paths.sh
source "$ROOT_DIR/wolf-cog-os/scripts/paths.sh"
# shellcheck source=../lib/substrate-resolve.sh
source "$ROOT_DIR/wolf-cog-os/scripts/lib/substrate-resolve.sh"

export COGOS_WORK="${COGOS_WORK:-$HOME/.cogos-forge-work}"
export COGOS_ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$COGOS_WORK/rootfs-forge}"
export COGOS_ROOTFS_SRC="$COGOS_ROOTFS_OUT"
export COGOS_FORGE_PROFILE="${COGOS_FORGE_PROFILE:-forge-selfhosted}"
export COGOS_TAG="${COGOS_TAG:-forge-substrate-test}"

PRIMARY_ISO="${COGOS_SUBSTRATE_ISO:-$REPO_ROOT/ubuntu-26.04-desktop-amd64.iso}"
PRIMARY_ID="${COGOS_SUBSTRATE_ID:-ubuntu-live}"

ROCKY_ISO=""
if ! ROCKY_ISO="$(substrate_resolve_rocky_iso_path)"; then
  ROCKY_ISO="$REPO_ROOT/rocky-substrate.iso"
fi

echo "=== Forge build with Rocky fallback ==="
echo "work:         $COGOS_WORK"
echo "rootfs_out:   $COGOS_ROOTFS_OUT"
echo "primary_iso:  $PRIMARY_ISO"
echo "primary_id:   $PRIMARY_ID"
echo "rocky_iso:    $ROCKY_ISO"

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK must be on native Linux fs (not /mnt/c or /mnt/e)" >&2
  exit 4
fi

sudo rm -rf "$COGOS_ROOTFS_OUT" 2>/dev/null || true
mkdir -p "$COGOS_WORK"

echo "[1/2] rootfs-forge (debootstrap on native ext4)..."
if ! sudo -E make rootfs-forge; then
  echo "ERROR: rootfs-forge failed — fix debootstrap before ISO step." >&2
  echo "       Ensure COGOS_ROOTFS_OUT=$COGOS_ROOTFS_OUT is on native Linux disk." >&2
  exit 1
fi

run_iso_tree() {
  local iso="$1"
  local sid="$2"
  export COGOS_SUBSTRATE_ISO="$iso"
  export COGOS_SUBSTRATE_ID="$sid"
  sudo -E ISO="$iso" make iso-tree-forge
}

echo "[2/2] iso-tree-forge (primary substrate)..."
if [[ -f "$PRIMARY_ISO" ]]; then
  if run_iso_tree "$PRIMARY_ISO" "$PRIMARY_ID"; then
    echo "PASS: Forge ISO built with primary substrate"
    ls -lh "$ROOT_DIR/wolf-cog-os/output/"*.iso 2>/dev/null || true
    exit 0
  fi
  echo "WARN: primary substrate ISO build failed — trying Rocky fallback"
else
  echo "WARN: primary ISO missing: $PRIMARY_ISO"
fi

if [[ ! -f "$ROCKY_ISO" ]]; then
  echo "No local Rocky ISO; fetching..."
  bash "$ROOT_DIR/wolf-cog-os/scripts/test/fetch-rocky-substrate.sh"
  ROCKY_ISO="$(substrate_resolve_rocky_iso_path)"
fi

echo "Retry iso-tree-forge with rocky-live ($ROCKY_ISO)..."
export COGOS_SUBSTRATE_ID=rocky-live
if run_iso_tree "$ROCKY_ISO" "rocky-live"; then
  echo "PASS: Forge ISO built with Rocky substrate fallback"
  ls -lh "$ROOT_DIR/wolf-cog-os/output/"*.iso 2>/dev/null || true
  exit 0
fi

echo "FAIL: both primary and Rocky substrate ISO builds failed" >&2
exit 1
