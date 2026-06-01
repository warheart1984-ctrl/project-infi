#!/usr/bin/env bash
# Fedora/RHEL/Rocky LiveOS replay adapter (nested squashfs.img + rootfs.img).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  local candidate
  SFS_SOURCE=""
  for candidate in \
    "$work_iso/LiveOS/squashfs.img" \
    "$work_iso/LiveOS/ext3fs.img" \
    "$work_iso/images/install.img" \
    "$(find "$work_iso/LiveOS" -maxdepth 1 -type f 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      SFS_SOURCE="$candidate"
      break
    fi
  done
  SFS_NAME="$(basename "${SFS_SOURCE:-squashfs.img}")"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  if [[ -n "${SFS_SOURCE:-}" ]]; then
    printf '%s\n' "$SFS_SOURCE"
    return 0
  fi
  adapter_resolve_sfs "$work_iso"
  printf '%s\n' "${SFS_SOURCE:-$work_iso/LiveOS/squashfs.img}"
}

adapter_workdir_ready() {
  local work="$1"
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/etc/os-release" ]] || return 1
}

adapter_extract_rootfs() {
  local _work_iso="$1"
  local rootfs_out="$2"
  adapter_resolve_sfs "$_work_iso"
  if [[ -z "${SFS_SOURCE:-}" || ! -f "$SFS_SOURCE" ]]; then
    echo "ERROR: fedora-liveos-layout: no LiveOS or images/install.img squashfs found" >&2
    return 4
  fi

  local stage="${rootfs_out}.liveos-stage"
  rm -rf "$stage" "$rootfs_out"
  mkdir -p "$stage" "$rootfs_out"

  echo "[fedora-liveos-layout] unsquashfs $SFS_NAME -> stage"
  if [[ "${COGOS_XATTRS:-0}" == "1" ]]; then
    unsquashfs -f -d "$stage" "$SFS_SOURCE"
  else
    unsquashfs -no-xattrs -f -d "$stage" "$SFS_SOURCE"
  fi

  if [[ -f "$stage/LiveOS/rootfs.img" ]]; then
    echo "[fedora-liveos-layout] mounting nested LiveOS/rootfs.img (Rocky/Fedora live)"
    local mnt="${stage}/loop-mnt"
    mkdir -p "$mnt"
    mount -o loop,ro "$stage/LiveOS/rootfs.img" "$mnt"
    rsync -aH "$mnt/" "$rootfs_out/"
    umount "$mnt" 2>/dev/null || true
  elif [[ -f "$stage/etc/os-release" ]]; then
    rsync -aH "$stage/" "$rootfs_out/"
  else
    rsync -aH "$stage/" "$rootfs_out/"
  fi

  rm -rf "$stage"
}
