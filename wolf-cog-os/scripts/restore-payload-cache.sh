#!/usr/bin/env bash
# Restore ~/.cogos-payload-cache from surprise/universal workdir + repo overlay fixes.
set -euo pipefail

CACHE="${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}"
REPO="/mnt/e/project-infi/wolf-cog-os/payload"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/ensure-payload-ready.sh
source "$SCRIPT_DIR/lib/ensure-payload-ready.sh"

export COGOS_PAYLOAD_SEED_FROM_SURPRISE=1
mkdir -p "$CACHE"
seed_payload_from_surprise "$CACHE" || exit 1

if [[ -d "$REPO" ]]; then
  echo "Overlaying repo install fixes..."
  copy_payload_tree_from_rootfs "$REPO" "$CACHE"
fi

bash "$SCRIPT_DIR/verify-full-runtime-release.sh"
echo "Payload cache ready: $CACHE"
