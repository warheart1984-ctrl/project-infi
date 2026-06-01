#!/usr/bin/env bash
# Android super.img / dynamic partition replay adapter (P15 universal substrate).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  SUPER_IMG=""
  BOOT_IMG=""
  SYSTEM_IMG=""
  local candidate
  for candidate in \
    "$work_iso/super.img" \
    "$(find "$work_iso" -maxdepth 3 -type f -name 'super.img' 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SUPER_IMG="$candidate"
      break
    fi
  done
  for candidate in \
    "$work_iso/boot.img" \
    "$(find "$work_iso" -maxdepth 3 -type f -name 'boot.img' 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      BOOT_IMG="$candidate"
      break
    fi
  done
  for candidate in \
    "$work_iso/system.img" \
    "$(find "$work_iso" -maxdepth 3 -type f -name 'system.img' 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SYSTEM_IMG="$candidate"
      break
    fi
  done
  SFS_SOURCE="${SUPER_IMG:-$SYSTEM_IMG}"
  SFS_NAME="$(basename "${SFS_SOURCE:-super.img}")"
  export ANDROID_SUPER_IMG="$SUPER_IMG"
  export ANDROID_BOOT_IMG="$BOOT_IMG"
  export ANDROID_SYSTEM_IMG="$SYSTEM_IMG"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  adapter_resolve_sfs "$work_iso"
  printf '%s\n' "${SFS_SOURCE:-$work_iso/super.img}"
}

adapter_workdir_ready() {
  local work="$1"
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/.forge-substrate-extracted" ]] || [[ -d "$work/rootfs/system" ]] || return 1
}

adapter_extract_rootfs() {
  local work_iso="$1"
  local rootfs_out="$2"
  adapter_resolve_sfs "$work_iso"
  if [[ -z "${SFS_SOURCE:-}" || ! -f "$SFS_SOURCE" ]]; then
    echo "ERROR: android-super-layout: no super.img/system.img found" >&2
    return 4
  fi

  mkdir -p "$rootfs_out"
  local part_dir="$work_iso/../partitions"
  mkdir -p "$part_dir"

  if [[ -n "${SUPER_IMG:-}" ]] && command -v lpunpack >/dev/null 2>&1; then
    echo "[android-super-layout] lpunpack super.img -> $part_dir"
    lpunpack "$SUPER_IMG" "$part_dir"
  elif [[ -n "${SYSTEM_IMG:-}" ]] && command -v simg2img >/dev/null 2>&1; then
    echo "[android-super-layout] simg2img system.img"
    simg2img "$SYSTEM_IMG" "$part_dir/system.raw" || cp -f "$SYSTEM_IMG" "$part_dir/system.img"
  else
    echo "ERROR: android-super-layout requires lpunpack (super.img) or simg2img (system.img)" >&2
    return 4
  fi

  mkdir -p "$rootfs_out/system" "$rootfs_out/vendor" "$rootfs_out/product"
  if [[ -f "$part_dir/system.img" ]]; then
    if command -v simg2img >/dev/null 2>&1; then
      simg2img "$part_dir/system.img" "$part_dir/system.raw" 2>/dev/null || true
    fi
    if [[ -f "$part_dir/system.raw" ]] && command -v mount >/dev/null 2>&1; then
      local mnt="${COGOS_ANDROID_MOUNT:-$part_dir/system-mnt}"
      mkdir -p "$mnt"
      mount -o loop,ro "$part_dir/system.raw" "$mnt" 2>/dev/null && {
        rsync -aH "$mnt/" "$rootfs_out/system/" || true
        umount "$mnt" 2>/dev/null || true
      }
    else
      cp -f "$part_dir/system.img" "$rootfs_out/system/system.img" 2>/dev/null || true
    fi
  fi
  for part in vendor product; do
    [[ -f "$part_dir/${part}.img" ]] && cp -f "$part_dir/${part}.img" "$rootfs_out/$part/${part}.img" 2>/dev/null || true
  done

  if [[ -n "${BOOT_IMG:-}" ]]; then
    mkdir -p "$rootfs_out/.forge/android"
    cp -f "$BOOT_IMG" "$rootfs_out/.forge/android/boot.img"
  fi

  # shellcheck source=inject-common.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../backends" && pwd)/inject-common.sh"
  inject_mark_extracted "$rootfs_out" "android"
}
