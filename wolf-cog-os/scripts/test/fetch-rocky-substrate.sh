#!/usr/bin/env bash
# Resolve or download Rocky Linux ISO for Forge substrate fallback.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# shellcheck source=../paths.sh
source "$ROOT_DIR/wolf-cog-os/scripts/paths.sh"
# shellcheck source=../lib/substrate-resolve.sh
source "$ROOT_DIR/wolf-cog-os/scripts/lib/substrate-resolve.sh"

OUT="${1:-}"
URL="${ROCKY_SUBSTRATE_URL:-https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.5-x86_64-boot.iso}"

if [[ -z "$OUT" ]]; then
  if resolved="$(substrate_resolve_rocky_iso_path)"; then
    OUT="$resolved"
    echo "=== Rocky substrate (existing) ==="
    echo "path: $OUT"
  else
    OUT="$REPO_ROOT/rocky-substrate.iso"
    echo "=== Fetch Rocky substrate ISO ==="
    echo "url:  $URL"
    echo "out:  $OUT"
    wget -O "$OUT" "$URL"
  fi
elif [[ ! -f "$OUT" ]]; then
  echo "ERROR: requested Rocky ISO not found: $OUT" >&2
  exit 2
fi

if [[ -f "$OUT" && "${COGOS_FORCE_FETCH:-0}" == "1" ]]; then
  echo "COGOS_FORCE_FETCH=1: re-downloading to $OUT"
  wget -O "$OUT" "$URL"
fi

ls -lh "$OUT"

mkdir -p ci-artifacts
python3 wolf-cog-os/scripts/validate-substrate.py \
  --iso "$OUT" \
  --substrate-id rocky-live \
  --mode fail \
  --output ci-artifacts/rocky-substrate-validation.json

echo "rocky substrate ready: $OUT"
echo "use: export COGOS_SUBSTRATE_ISO=$OUT COGOS_SUBSTRATE_ID=rocky-live"
