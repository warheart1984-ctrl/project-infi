#!/usr/bin/env bash
# Wolf CoG OS — Forge self-hosting ISO builder
#
# Builds a Forge ISO that boots into a controlled build environment with /forge mounted.
#
# Usage:
#   bash wolf-cog-os/scripts/build-forge-installer.sh [substrate.iso]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/substrate-resolve.sh
source "$SCRIPT_DIR/lib/substrate-resolve.sh"
# shellcheck source=lib/update-full-runtime-manifest.sh
source "$SCRIPT_DIR/lib/update-full-runtime-manifest.sh"
# shellcheck source=lib/ensure-payload-ready.sh
source "$SCRIPT_DIR/lib/ensure-payload-ready.sh"

TAG="${COGOS_TAG:-wolf-cog-os-forge-1.0}"
BUILD_DATE="${COGOS_BUILD_DATE:-$(date -u +%Y-%m-%d)}"
FORGE_PROFILE="${COGOS_FORGE_PROFILE:-forge-selfhosted}"

export COGOS_TAG="$TAG"
export COGOS_BUILD_DATE="$BUILD_DATE"
export COGOS_FORGE_PROFILE="$FORGE_PROFILE"
export COGOS_BOOT_PROFILE=forge
export COGOS_ENABLE_PID1=0
export COGOS_METAL_INSTALL=1
export COGOS_STEALTH_INSTALL=0
export COGOS_SURPRISE_INSTALL=0
export COGOS_FULL_RUNTIME=0
export COGOS_GRUB_MERGE=1
export COGOS_LIVE_FINDISO=0
export COGOS_BUILD_FROM_TREE=1
export COGOS_BUILD_ROOTFS_FIRST="${COGOS_BUILD_ROOTFS_FIRST:-1}"
export COGOS_DAILY_DRIVER_PACKAGES=0
export COGOS_PLYMOUTH_POLICY="${COGOS_PLYMOUTH_POLICY:-optional}"
export COGOS_SQUASHFS_COMP="${COGOS_SQUASHFS_COMP:-xz}"
export COGOS_WORK="${COGOS_FORGE_WORK:-${HOME}/.cogos-forge-installer-work}"

BASE_ISO="${1:-$(substrate_resolve_iso_path "" 2>/dev/null || true)}"
if [[ -z "$BASE_ISO" ]]; then
  BASE_ISO="${COGOS_SUBSTRATE_ISO:-${COGOS_DEBIAN_ISO:-$DEBIAN_BASE_ISO}}"
fi
if [[ ! -f "$BASE_ISO" && -f "${HOME}/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
  BASE_ISO="${HOME}/debian-live-13.5.0-amd64-cinnamon.iso"
fi

if [[ ! -f "$BASE_ISO" ]]; then
  echo "ERROR: Substrate ISO not found: ${BASE_ISO:-<unset>}" >&2
  echo "Pass any compatible live hybrid ISO path, or set COGOS_SUBSTRATE_ISO." >&2
  exit 3
fi

substrate_export_env "$BASE_ISO"
SUBSTRATE_ID="${COGOS_SUBSTRATE_ID:-auto}"
python3 "$SCRIPT_DIR/validate-substrate.py" \
  --iso "$BASE_ISO" \
  --substrate-id "$SUBSTRATE_ID" \
  --registry "$COGOS_SUBSTRATE_REGISTRY" \
  --mode "${COGOS_SUBSTRATE_VALIDATION_MODE:-fail}" \
  --output "${COGOS_CI_ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}/substrate-validation.json"

export COGOS_BOOT_REPLAY_ISO="${COGOS_BOOT_REPLAY_ISO:-$BASE_ISO}"

COGOS_OUT_FINAL="${COGOS_OUT:-$REPO_ROOT/Wolf-CoG-OS-forge-selfhosted.iso}"
if [[ "$COGOS_OUT_FINAL" == /mnt/* ]]; then
  export COGOS_OUT="${HOME}/Wolf-CoG-OS-forge-selfhosted.iso"
else
  export COGOS_OUT="$COGOS_OUT_FINAL"
fi

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK on Windows mount (9p) breaks unsquashfs symlinks." >&2
  exit 4
fi

PAYLOAD_CACHE="${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}"
ensure_payload_ready "$WOLF_PAYLOAD" "$PAYLOAD_CACHE"

MANIFEST_ROOT="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}/opt/cogos"
update_full_runtime_manifest "$MANIFEST_ROOT" "$TAG" "$BUILD_DATE" "forge"

echo "=== Wolf CoG OS Forge ISO ==="
echo "Tag:        $COGOS_TAG"
echo "Profile:    $COGOS_FORGE_PROFILE"
echo "Substrate:  $BASE_ISO (id=${SUBSTRATE_ID})"
echo "Boot menu:  Run CoGOS | Enter Forge Mode | Recovery"
echo "Output:     $COGOS_OUT"
echo "Work:       $COGOS_WORK"

bash "$SCRIPT_DIR/build.sh" --profile "$FORGE_PROFILE" "$BASE_ISO"

if [[ "$COGOS_OUT" != "$COGOS_OUT_FINAL" ]]; then
  cp -f "$COGOS_OUT" "${COGOS_OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $COGOS_OUT" >&2
fi

echo ""
echo "=== Wolf CoG OS Forge ISO complete ==="
echo "Boot menu:"
echo "  - Run CoGOS (Normal)"
echo "  - Enter Forge Mode (pipeline cockpit at /forge)"
echo "  - Recovery / Debug Shell"
echo "Inside Forge Mode:"
echo "  forge-menu"
echo "SHA: ${COGOS_OUT}.sha256"
ls -lh "$COGOS_OUT" "${COGOS_OUT}.sha256" 2>/dev/null || true
