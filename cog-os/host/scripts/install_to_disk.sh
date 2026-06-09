#!/usr/bin/env bash
# Install Nova NorthStar CoG OS rootfs to a block device (UEFI-aware installer).
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <rootfs-dir> <block-device>" >&2
  exit 1
fi

ROOTFS="$1"
DEVICE="$2"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

exec bash "$REPO_ROOT/cog-os/scripts/cogos-installer.sh" \
  --apply \
  --yes \
  --non-interactive \
  --rootfs "$ROOTFS" \
  --target-disk "$DEVICE"
