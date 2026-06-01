#!/usr/bin/env bash
# Android system/vendor overlay customization (init scripts, sepolicy overlays).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_chroot_customize() {
  local rootfs_out="$1"
  local manifest="${COGOS_INJECT_MANIFEST:-$WOLF_COGOS_ROOT/config/overlays/android-inject/manifest.json}"

  echo "[android-backend] applying Android overlay manifest (SELinux labels require host restorecon in production)"
  inject_apply_manifest "$rootfs_out" "$manifest"

  for layer in system vendor product; do
    if [[ -d "$WOLF_COGOS_ROOT/config/overlays/android-inject/$layer" ]]; then
      mkdir -p "$rootfs_out/$layer"
      rsync -a "$WOLF_COGOS_ROOT/config/overlays/android-inject/$layer/" "$rootfs_out/$layer/" 2>/dev/null || true
    fi
  done

  if [[ -f "$WOLF_COGOS_ROOT/config/overlays/android-inject/init.rc.fragment" ]]; then
    mkdir -p "$rootfs_out/system/etc/init"
    cp -f "$WOLF_COGOS_ROOT/config/overlays/android-inject/init.rc.fragment" "$rootfs_out/system/etc/init/forge.rc" 2>/dev/null || true
  fi
}
