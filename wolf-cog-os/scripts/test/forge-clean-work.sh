#!/usr/bin/env bash
# Remove scoped Forge / substrate smoke work dirs (native Linux fs only).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

TAG_SAFE="${COGOS_TAG:-forge-rocky-test}"
TAG_SAFE="${TAG_SAFE//[^A-Za-z0-9]/-}"

DIRS=(
  "${COGOS_WORK:-$HOME/.cogos-forge-work/scratch}"
  "${COGOS_ROOTFS_OUT:-$HOME/.cogos-forge-work/rootfs-forge}"
  "${COGOS_ROOTFS_WORK:-$HOME/.cogos-forge-work/rootfs-stage}"
  "$HOME/.cogos-forge-work/scratch"
  "$HOME/.cogos-forge-work/rootfs-forge"
  "$HOME/.cogos-forge-work/rootfs-stage"
  "$HOME/.forge-ubuntu-smoke"
  "/tmp/wolf-cog-os-build-${TAG_SAFE}"
  "/tmp/wolf-cog-os-build-${TAG_SAFE}-rootfs-stage"
  "/tmp/wolf-cog-os-build-12-22-0-wolf-os"
  "/tmp/wolf-cog-os-build-12-22-0-wolf-os-rootfs-stage"
)

forge_remove_dir() {
  local dir="$1"
  if rm -rf "$dir" 2>/dev/null; then
    return 0
  fi
  if sudo -n rm -rf "$dir" 2>/dev/null; then
    return 0
  fi
  echo "WARN: could not remove $dir (run: sudo rm -rf '$dir')" >&2
}

echo "=== Forge work cleanup ==="
for dir in "${DIRS[@]}"; do
  [[ -z "$dir" ]] && continue
  if [[ -e "$dir" ]]; then
    echo "remove: $dir"
    forge_remove_dir "$dir"
  fi
done

# Partial rootfs on DrvFs (debootstrap tar failures) — repo-local only
if [[ -d "$ROOT_DIR/wolf-cog-os/build" ]]; then
  for dir in "$ROOT_DIR/wolf-cog-os/build"/rootfs-*; do
    [[ -e "$dir" ]] || continue
    echo "remove: $dir"
    forge_remove_dir "$dir"
  done
fi

echo "cleanup done"
