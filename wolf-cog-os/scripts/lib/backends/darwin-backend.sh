#!/usr/bin/env bash
# macOS darwin inject backend (P15 — overlay LaunchDaemons/profiles on APFS tree).
set -euo pipefail

# shellcheck source=inject-common.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/inject-common.sh"

backend_bootstrap() {
  local rootfs_out="$1"
  mkdir -p "$rootfs_out"
  if [[ ! -f "$rootfs_out/.forge-substrate-extracted" ]]; then
    echo "[darwin-backend] awaiting APFS replay-extracted rootfs"
  fi
  echo "[1/7] Darwin inject backend (overlay-only)"
}
