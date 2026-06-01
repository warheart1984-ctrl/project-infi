#!/usr/bin/env bash
# Copy canonical release payload from WSL cache into wolf-cog-os/payload (for git/release).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

CACHE="${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}"
DEST="$WOLF_PAYLOAD"

if [[ ! -f "$CACHE/opt/cogos/config/release_manifest.json" ]]; then
  echo "ERROR: payload cache missing at $CACHE" >&2
  exit 1
fi

echo "Syncing release payload:"
echo "  from: $CACHE"
echo "  to:   $DEST"

rsync -a --delete \
  --exclude 'opt/cogos/memory/' \
  --exclude '**/__pycache__/' \
  --exclude '*.pyc' \
  "$CACHE/" "$DEST/"

echo "Done. Run: bash wolf-cog-os/scripts/verify-full-runtime-release.sh"
