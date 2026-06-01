#!/usr/bin/env bash
# Arch pacstrap backend (P11 production on Arch-capable hosts).
set -euo pipefail

backend_bootstrap() {
  local rootfs_out="$1"
  local mirror="${COGOS_ARCH_MIRROR:-https://geo.mirror.pkgbuild.com/}"
  local arch="${COGOS_ARCH:-x86_64}"
  local pkg_file="${COGOS_ARCH_PACKAGES:-$WOLF_COGOS_ROOT/config/packages/arch-base.txt}"
  local -a packages=()

  for tool in pacstrap arch-chroot; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      echo "ERROR: $tool not found for pacstrap backend" >&2
      echo "       Install arch-install-scripts on an Arch host or set COGOS_ROOTFS_BACKEND=debootstrap" >&2
      exit 3
    fi
  done

  if [[ -f "$pkg_file" ]]; then
    mapfile -t packages < <(grep -Ev '^\s*(#|$)' "$pkg_file")
  fi
  if [[ ${#packages[@]} -eq 0 ]]; then
    packages=(base systemd sudo bash openssh pacman networkmanager)
  fi

  echo "[1/7] Bootstrap Arch rootfs via pacstrap backend ($arch, ${#packages[@]} packages)"
  pacstrap -K "$rootfs_out" "${packages[@]}"
}
