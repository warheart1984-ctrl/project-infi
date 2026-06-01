#!/usr/bin/env bash
# Rootfs backend bootstrap dispatcher.
set -euo pipefail

rootfs_backend_registry_path() {
  echo "${COGOS_ROOTFS_BACKEND_REGISTRY:-$WOLF_FORGE_STAGING/backends/registry.json}"
}

rootfs_bootstrap() {
  local rootfs_out="$1"
  local backend="${COGOS_ROOTFS_BACKEND:-debootstrap}"
  local module="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}/lib/backends/${backend}.sh"

  if [[ ! -f "$module" ]]; then
    echo "ERROR: unknown rootfs backend module: $backend ($module)" >&2
    echo "       See wolf-cog-os/forge/backends/registry.json" >&2
    exit 3
  fi

  # shellcheck source=/dev/null
  source "$module"
  if ! declare -F backend_bootstrap >/dev/null 2>&1; then
    echo "ERROR: backend module $backend does not define backend_bootstrap()" >&2
    exit 3
  fi
  backend_bootstrap "$rootfs_out"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  # shellcheck source=paths.sh
  source "$_dir/paths.sh"
  SCRIPT_DIR="$(cd "$_dir/.." && pwd)"
  rootfs_bootstrap "${1:-$WOLF_ROOTFS_OUT}"
fi
