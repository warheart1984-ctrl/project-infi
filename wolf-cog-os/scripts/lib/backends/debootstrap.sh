#!/usr/bin/env bash
# Debian debootstrap backend (production).
set -euo pipefail

backend_bootstrap() {
  local rootfs_out="$1"
  local suite="${COGOS_DEBIAN_SUITE:-trixie}"
  local mirror="${COGOS_MIRROR:-http://deb.debian.org/debian}"
  local arch="${COGOS_ARCH:-amd64}"

  if ! command -v debootstrap >/dev/null 2>&1; then
    echo "ERROR: debootstrap not found for backend debootstrap" >&2
    exit 3
  fi

  echo "[1/7] Bootstrap Debian rootfs via debootstrap backend ($suite / $arch)"
  debootstrap --arch="$arch" --variant=minbase "$suite" "$rootfs_out" "$mirror"
}
