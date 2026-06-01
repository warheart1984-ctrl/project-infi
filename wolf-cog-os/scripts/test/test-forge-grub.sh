#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TMP_WORK="$(mktemp -d "${TMPDIR:-/tmp}/forge-grub-test.XXXXXX")"

cleanup() {
  rm -rf "$TMP_WORK"
}
trap cleanup EXIT

export WORK="$TMP_WORK/iso-work"
mkdir -p "$WORK/iso/live" "$WORK/iso/boot/grub"
touch "$WORK/iso/live/vmlinuz-6.1.0" "$WORK/iso/live/initrd.img"

# shellcheck source=../../patch_grub_merge.sh
source "$ROOT_DIR/wolf-cog-os/scripts/patch_grub_merge.sh"

patch_grub_forge

GRUB_CFG="$WORK/iso/boot/grub/grub.cfg"
for needle in \
  "Run CoGOS (Normal)" \
  "Enter Forge Mode" \
  "Recovery / Debug Shell" \
  "cogos.forge=1"; do
  if ! grep -q "$needle" "$GRUB_CFG"; then
    echo "FAIL: missing GRUB entry marker: $needle" >&2
    exit 1
  fi
done

echo "forge GRUB template checks passed"
