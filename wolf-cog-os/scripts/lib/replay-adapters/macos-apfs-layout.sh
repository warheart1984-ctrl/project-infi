#!/usr/bin/env bash
# macOS APFS / Installer.app replay adapter (P15 universal substrate).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  APFS_DMG=""
  SYSTEM_DMG=""
  local candidate
  for candidate in \
    "$work_iso/BaseSystem.dmg" \
    "$(find "$work_iso" -maxdepth 3 -type f -name 'BaseSystem.dmg' 2>/dev/null | head -n 1)" \
    "$(find "$work_iso" -maxdepth 3 -type f -name 'InstallAssistant.pkg' 2>/dev/null | head -n 1)" \
    "$(find "$work_iso" -maxdepth 4 -type f -name 'InstallESD.dmg' 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      APFS_DMG="$candidate"
      break
    fi
  done
  for candidate in \
    "$(find "$work_iso" -maxdepth 4 -type f -name 'SharedSupport.dmg' 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SYSTEM_DMG="$candidate"
      break
    fi
  done
  SFS_SOURCE="$APFS_DMG"
  SFS_NAME="$(basename "${SFS_SOURCE:-BaseSystem.dmg}")"
  export MACOS_APFS_DMG="$APFS_DMG"
  export MACOS_SYSTEM_DMG="$SYSTEM_DMG"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  adapter_resolve_sfs "$work_iso"
  printf '%s\n' "${SFS_SOURCE:-$work_iso/BaseSystem.dmg}"
}

adapter_workdir_ready() {
  local work="$1"
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/.forge-substrate-extracted" ]] || [[ -d "$work/rootfs/System" ]] || return 1
}

adapter_extract_rootfs() {
  local work_iso="$1"
  local rootfs_out="$2"
  adapter_resolve_sfs "$work_iso"
  if [[ -z "${SFS_SOURCE:-}" || ! -f "$SFS_SOURCE" ]]; then
    echo "ERROR: macos-apfs-layout: no BaseSystem.dmg / InstallAssistant.pkg found" >&2
    return 4
  fi

  mkdir -p "$rootfs_out"
  local mount_dir="${COGOS_APFS_MOUNT:-$work_iso/../.forge-apfs-mount}"
  mkdir -p "$mount_dir"

  if command -v hdiutil >/dev/null 2>&1; then
    echo "[macos-apfs-layout] hdiutil attach + APFS mount (native macOS host required for production)"
    hdiutil attach -nobrowse -mountpoint "$mount_dir" "$SFS_SOURCE" >/dev/null
    rsync -aH "$mount_dir/" "$rootfs_out/" || {
      hdiutil detach "$mount_dir" >/dev/null 2>&1 || true
      return 4
    }
    hdiutil detach "$mount_dir" >/dev/null 2>&1 || true
  elif command -v dmg2img >/dev/null 2>&1; then
    local raw_img="${COGOS_APFS_RAW:-$rootfs_out/.forge/macos-base.raw}"
    mkdir -p "$(dirname "$raw_img")"
    echo "[macos-apfs-layout] dmg2img -> raw (APFS mount requires apfs-fuse on Linux)"
    dmg2img "$SFS_SOURCE" "$raw_img"
    if command -v mount >/dev/null 2>&1 && command -v apfs-fuse >/dev/null 2>&1; then
      mount -t apfs -o loop "$raw_img" "$mount_dir" 2>/dev/null || true
      if mountpoint -q "$mount_dir" 2>/dev/null; then
        rsync -aH "$mount_dir/" "$rootfs_out/" || true
        umount "$mount_dir" 2>/dev/null || true
      fi
    fi
    if [[ ! -f "$rootfs_out/.forge-substrate-extracted" && ! -d "$rootfs_out/System" ]]; then
      echo "ERROR: macos-apfs-layout: APFS extraction incomplete on this host" >&2
      echo "       Requires macOS (hdiutil) or Linux apfs-fuse after dmg2img" >&2
      return 4
    fi
  else
    echo "ERROR: macos-apfs-layout requires hdiutil (macOS) or dmg2img+apfs-fuse (Linux)" >&2
    return 4
  fi

  mkdir -p "$rootfs_out/.forge/macos"
  [[ -n "${SYSTEM_DMG:-}" ]] && cp -f "$SYSTEM_DMG" "$rootfs_out/.forge/macos/SharedSupport.dmg" 2>/dev/null || true

  # shellcheck source=inject-common.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../backends" && pwd)/inject-common.sh"
  inject_mark_extracted "$rootfs_out" "macos"
}
