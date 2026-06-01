#!/usr/bin/env bash
# Android inject backend (P15 — overlay system/vendor + boot.img hooks).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_bootstrap() {
  local rootfs_out="$1"
  mkdir -p "$rootfs_out"/{system,vendor,product}
  if [[ ! -f "$rootfs_out/.forge-substrate-extracted" ]]; then
    echo "[android-backend] awaiting super.img replay-extracted partitions"
  fi
  echo "[1/7] Android inject backend (overlay/repack-only)"
}
