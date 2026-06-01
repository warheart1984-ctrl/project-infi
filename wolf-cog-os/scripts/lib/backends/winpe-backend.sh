#!/usr/bin/env bash
# Windows WinPE inject backend (P15 — extract via replay, inject drivers/config/registry).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_bootstrap() {
  local rootfs_out="$1"
  mkdir -p "$rootfs_out"
  if [[ ! -f "$rootfs_out/.forge-substrate-extracted" ]]; then
    echo "[winpe-backend] awaiting replay-extracted rootfs (run build.sh with windows substrate first)"
    echo "              or set COGOS_BUILD_FROM_TREE=1 with pre-staged Windows tree"
  fi
  echo "[1/7] WinPE inject backend (no debootstrap — injection-only)"
}
