#!/usr/bin/env bash
# macOS darwin overlay customization (LaunchDaemons, profiles, payloads).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_chroot_customize() {
  local rootfs_out="$1"
  local manifest="${COGOS_INJECT_MANIFEST:-$WOLF_COGOS_ROOT/config/overlays/macos-inject/manifest.json}"

  echo "[darwin-backend] applying macOS overlay manifest (sealed snapshot invariants external)"
  inject_apply_manifest "$rootfs_out" "$manifest"

  for src_dst in \
    "LaunchDaemons:Library/LaunchDaemons" \
    "LaunchAgents:Library/LaunchAgents" \
    "ConfigurationProfiles:Library/Managed Preferences"; do
    src="${src_dst%%:*}"
    dst="${src_dst##*:}"
    if [[ -d "$WOLF_COGOS_ROOT/config/overlays/macos-inject/$src" ]]; then
      mkdir -p "$rootfs_out/$dst"
      rsync -a "$WOLF_COGOS_ROOT/config/overlays/macos-inject/$src/" "$rootfs_out/$dst/" 2>/dev/null || true
    fi
  done
}
