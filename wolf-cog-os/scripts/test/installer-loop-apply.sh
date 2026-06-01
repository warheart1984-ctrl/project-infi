#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
ROOTFS_SRC="${COGOS_ROOTFS_SRC:-$ROOT_DIR/wolf-cog-os/build/rootfs-${COGOS_TAG:-12-22-0-wolf-os}}"
STATE_DIR="${INSTALLER_STATE_DIR:-/tmp/cogos-installer-loop}"
WORK_DIR="${COGOS_LOOP_TEST_WORK:-/tmp/cogos-loop-test}"
IMG_PATH="${COGOS_LOOP_TEST_IMG:-$WORK_DIR/disk.img}"
IMG_SIZE="${COGOS_LOOP_TEST_SIZE:-20G}"
TARGET_MOUNT_ROOT="${TARGET_MOUNT_ROOT:-$WORK_DIR/target-root}"
INSTALLER_HOSTNAME="${COGOS_LOOP_TEST_HOSTNAME:-cogos-loop-test}"
INSTALLER_USER="${COGOS_LOOP_TEST_USER:-operator}"
INSTALLER_EXTRA_ARGS="${INSTALLER_EXTRA_ARGS:-}"
LOOP_REUSE_IMG="${COGOS_LOOP_REUSE_IMG:-0}"
LOOP_DEV=""

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing command: $1" >&2; exit 2; }
}

cleanup() {
  if [[ -n "$LOOP_DEV" ]]; then
    sudo losetup -d "$LOOP_DEV" 2>/dev/null || true
  fi
  sudo umount -lf "$TARGET_MOUNT_ROOT/proc" 2>/dev/null || true
  sudo umount -lf "$TARGET_MOUNT_ROOT/sys" 2>/dev/null || true
  sudo umount -lf "$TARGET_MOUNT_ROOT/dev" 2>/dev/null || true
  sudo umount -lf "$TARGET_MOUNT_ROOT/boot/efi" 2>/dev/null || true
  sudo umount -lf "$TARGET_MOUNT_ROOT/opt/cogos/data" 2>/dev/null || true
  sudo umount -lf "$TARGET_MOUNT_ROOT" 2>/dev/null || true
}
trap cleanup EXIT

require qemu-img
require losetup
require python3

if [[ ! -d "$ROOTFS_SRC" ]]; then
  echo "Rootfs source not found: $ROOTFS_SRC" >&2
  exit 3
fi

mkdir -p "$WORK_DIR" "$STATE_DIR" "$TARGET_MOUNT_ROOT"
if [[ "$LOOP_REUSE_IMG" != "1" ]]; then
  rm -f "$IMG_PATH"
  qemu-img create -f raw "$IMG_PATH" "$IMG_SIZE"
elif [[ ! -f "$IMG_PATH" ]]; then
  qemu-img create -f raw "$IMG_PATH" "$IMG_SIZE"
fi

LOOP_DEV="$(sudo losetup --find --show "$IMG_PATH")"
echo "Loop device: $LOOP_DEV"

sudo INSTALLER_STATE_DIR="$STATE_DIR" TARGET_MOUNT_ROOT="$TARGET_MOUNT_ROOT" \
  bash "$ROOT_DIR/wolf-cog-os/scripts/cogos-installer.sh" \
    --target-disk "$LOOP_DEV" \
    --rootfs "$ROOTFS_SRC" \
    --hostname "$INSTALLER_HOSTNAME" \
    --user "$INSTALLER_USER" \
    --apply --yes --non-interactive $INSTALLER_EXTRA_ARGS

python3 "$ROOT_DIR/wolf-cog-os/scripts/test/validate-installer-state.py" \
  --state "$STATE_DIR/state.json" \
  --require-proof \
  --target-root "$TARGET_MOUNT_ROOT"

echo "Loopback installer integration test passed."
