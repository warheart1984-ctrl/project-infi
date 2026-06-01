#!/usr/bin/env bash
# Clean forge work dirs, build rootfs on native fs, iso-tree with local Rocky ISO.
# One sudo session = one password prompt.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

FORGE_BASE="${FORGE_BASE:-$HOME/.cogos-forge-work}"
export COGOS_TAG="${COGOS_TAG:-forge-rocky-test}"
export COGOS_WORK="${COGOS_WORK:-$FORGE_BASE/scratch}"
export COGOS_ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$FORGE_BASE/rootfs-forge}"
export COGOS_ROOTFS_WORK="${COGOS_ROOTFS_WORK:-$FORGE_BASE/rootfs-stage}"
export COGOS_ROOTFS_SRC="$COGOS_ROOTFS_OUT"
export COGOS_FORGE_PROFILE="${COGOS_FORGE_PROFILE:-forge-selfhosted}"
unset COGOS_SUBSTRATE_ID COGOS_SUBSTRATE_ISO

# shellcheck source=../paths.sh
source "$ROOT_DIR/wolf-cog-os/scripts/paths.sh"
# shellcheck source=../lib/substrate-resolve.sh
source "$ROOT_DIR/wolf-cog-os/scripts/lib/substrate-resolve.sh"

ROCKY_ISO="$(substrate_resolve_rocky_iso_path)" || {
  echo "ERROR: no Rocky ISO found under $REPO_ROOT (expected Rocky-*.iso)" >&2
  exit 2
}

export COGOS_SUBSTRATE_ISO="$ROCKY_ISO"
export COGOS_SUBSTRATE_ID=rocky-live

echo "=== Forge Rocky build ==="
echo "work:       $COGOS_WORK"
echo "rootfs_out: $COGOS_ROOTFS_OUT"
echo "rocky_iso:  $ROCKY_ISO"
echo "substrate:  $COGOS_SUBSTRATE_ID"

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK must be on native Linux fs (not /mnt/c or /mnt/e)" >&2
  exit 4
fi

bash "$ROOT_DIR/wolf-cog-os/scripts/test/forge-clean-work.sh"

ROOTFS_MARKER="$COGOS_ROOTFS_OUT/etc/os-release"
BUILD_ROOTFS=1
if [[ -f "$ROOTFS_MARKER" ]]; then
  echo "rootfs already built at $COGOS_ROOTFS_OUT — skipping rootfs-forge"
  BUILD_ROOTFS=0
fi

sudo -E bash <<ROOT
set -euo pipefail
cd "$ROOT_DIR"
export COGOS_TAG="$COGOS_TAG"
export COGOS_WORK="$COGOS_WORK"
export COGOS_ROOTFS_OUT="$COGOS_ROOTFS_OUT"
export COGOS_ROOTFS_WORK="$COGOS_ROOTFS_WORK"
export COGOS_ROOTFS_SRC="$COGOS_ROOTFS_SRC"
export COGOS_FORGE_PROFILE="$COGOS_FORGE_PROFILE"
export COGOS_SUBSTRATE_ISO="$ROCKY_ISO"
export COGOS_SUBSTRATE_ID=rocky-live
export COGOS_BUILD_FROM_TREE=1

if [[ "$BUILD_ROOTFS" == "1" ]]; then
  echo "[1/2] rootfs-forge..."
  bash "$ROOT_DIR/wolf-cog-os/scripts/build-rootfs.sh" --profile "$COGOS_FORGE_PROFILE"
else
  echo "[1/2] rootfs-forge skipped (existing tree)"
fi

echo "[2/2] iso-tree-forge (rocky-live)..."
bash "$ROOT_DIR/wolf-cog-os/scripts/build.sh" --profile "$COGOS_FORGE_PROFILE" "$ROCKY_ISO"
ROOT

echo "PASS: Rocky substrate Forge build finished"
ls -lh "$ROOT_DIR/wolf-cog-os/output/"*.iso 2>/dev/null || true
