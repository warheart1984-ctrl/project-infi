#!/usr/bin/env bash
# Rootfs chroot customization dispatcher (P11).
set -euo pipefail

rootfs_chroot_customize() {
  local rootfs_out="$1"
  local backend="${COGOS_ROOTFS_BACKEND:-debootstrap}"
  local module=""
  case "$backend" in
    winpe-backend) module="${SCRIPT_DIR}/lib/backends/chroot-winpe.sh" ;;
    darwin-backend) module="${SCRIPT_DIR}/lib/backends/chroot-darwin.sh" ;;
    android-backend) module="${SCRIPT_DIR}/lib/backends/chroot-android.sh" ;;
    pacstrap) module="${SCRIPT_DIR}/lib/backends/chroot-pacstrap.sh" ;;
    debootstrap|dnfroot|apkroot|*) module="${SCRIPT_DIR}/lib/backends/chroot-debian.sh" ;;
  esac
  # shellcheck source=/dev/null
  source "$module"
  if ! declare -F backend_chroot_customize >/dev/null 2>&1; then
    echo "ERROR: chroot module for backend $backend missing backend_chroot_customize()" >&2
    exit 3
  fi
  backend_chroot_customize "$rootfs_out"
}
