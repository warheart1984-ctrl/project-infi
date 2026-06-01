#!/usr/bin/env bash
# Debian/Ubuntu/cogos live/filesystem.squashfs replay adapter (production).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  local candidate
  SFS_SOURCE=""
  for candidate in \
    "$work_iso/casper/filesystem.squashfs" \
    "$work_iso/casper/minimal.standard.live.squashfs" \
    "$work_iso/casper/minimal.standard.enhanced-secureboot.live.squashfs" \
    "$(find "$work_iso/casper" -maxdepth 1 -type f -name '*live*.squashfs' 2>/dev/null | sort | head -n 1)" \
    "$work_iso/live/filesystem.squashfs" \
    "$(find "$work_iso/live" -maxdepth 1 -type f -name 'filesystem*.squashfs' 2>/dev/null | head -n 1)" \
    "$(find "$work_iso/casper" -maxdepth 1 -type f -name '*.squashfs' 2>/dev/null | sort | head -n 1)" \
    "$(find "$work_iso" -maxdepth 3 -type f -name '*.squashfs' 2>/dev/null | sort | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SFS_SOURCE="$candidate"
      break
    fi
  done
  SFS_NAME="$(basename "${SFS_SOURCE:-filesystem.squashfs}")"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  if [[ -n "${SFS_SOURCE:-}" ]]; then
    printf '%s\n' "$SFS_SOURCE"
    return 0
  fi
  printf '%s\n' "$work_iso/live/filesystem.squashfs"
}

adapter_workdir_ready() {
  local work="$1"
  [[ -d "$work/iso/live" || -d "$work/iso/casper" ]] || return 1
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/etc/os-release" ]] || return 1
}

adapter_extract_rootfs() {
  local _work_iso="$1"
  local rootfs_out="$2"
  if [[ -z "${SFS_SOURCE:-}" || ! -f "$SFS_SOURCE" ]]; then
    echo "ERROR: debian-live-layout: no squashfs source resolved" >&2
    return 4
  fi
  if [[ "${COGOS_XATTRS:-0}" == "1" ]]; then
    unsquashfs -f -d "$rootfs_out" "$SFS_SOURCE"
  else
    unsquashfs -no-xattrs -f -d "$rootfs_out" "$SFS_SOURCE"
  fi
}
