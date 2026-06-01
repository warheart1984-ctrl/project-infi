#!/usr/bin/env bash
# Windows WinPE injection customization (drivers, registry hives, provisioning).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_chroot_customize() {
  local rootfs_out="$1"
  local manifest="${COGOS_INJECT_MANIFEST:-$WOLF_COGOS_ROOT/config/overlays/windows-inject/manifest.json}"

  echo "[winpe-backend] applying Windows inject manifest (BCD/signature invariants preserved)"
  inject_apply_manifest "$rootfs_out" "$manifest"

  if [[ -d "$WOLF_COGOS_ROOT/config/overlays/windows-inject/drivers" ]]; then
    mkdir -p "$rootfs_out/drivers/injected"
    rsync -a "$WOLF_COGOS_ROOT/config/overlays/windows-inject/drivers/" "$rootfs_out/drivers/injected/" 2>/dev/null || true
  fi
  if [[ -d "$WOLF_COGOS_ROOT/config/overlays/windows-inject/registry" ]]; then
    mkdir -p "$rootfs_out/Windows/System32/config/ForgeInject"
    rsync -a "$WOLF_COGOS_ROOT/config/overlays/windows-inject/registry/" "$rootfs_out/Windows/System32/config/ForgeInject/" 2>/dev/null || true
  fi
}
