#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$FORGE_DIR/../.." && pwd)"

PROFILE="${COG_PROFILE:-metal}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    -h|--help)
      echo "usage: $0 [--profile metal|daily-driver]"
      exit 0
      ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

# shellcheck source=lib/profile-loader.sh
source "$SCRIPT_DIR/lib/profile-loader.sh" --profile "$PROFILE" --export

ROOTFS="${COG_ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-$PROFILE}"
rm -rf "$ROOTFS"
mkdir -p "$(dirname "$ROOTFS")"

COG_PROFILE="$PROFILE" COG_PACKAGE_LIST="$COG_PACKAGE_LIST" \
  COG_EXCLUDE_SYSTEMD="$COG_EXCLUDE_SYSTEMD" \
  bash "$REPO_ROOT/cog-os/host/scripts/build_rootfs.sh" "$ROOTFS"

# shellcheck source=lib/resolve-rootfs.sh
source <(sed 's/\r$//' "$SCRIPT_DIR/lib/resolve-rootfs.sh")
EFFECTIVE_ROOTFS="$(resolve_cog_rootfs "$ROOTFS")"

bash "$SCRIPT_DIR/lib/render-init-conf.sh" --profile "$PROFILE" --output "$EFFECTIVE_ROOTFS/etc/init.conf"
chmod 0644 "$EFFECTIVE_ROOTFS/etc/init.conf"

COG_PAYLOAD_UL="${COG_PAYLOAD_UL:-0}" bash "$SCRIPT_DIR/lib/payload-stage.sh" "$EFFECTIVE_ROOTFS"

if [[ "$PROFILE" == "daily-driver" ]]; then
  bash "$SCRIPT_DIR/lib/install-daily-driver-session.sh" "$EFFECTIVE_ROOTFS"
fi

bash "$SCRIPT_DIR/lib/emit-profile-attestation.sh" --profile "$PROFILE" --rootfs "$EFFECTIVE_ROOTFS"

echo "Nova NorthStar CoG OS rootfs: $EFFECTIVE_ROOTFS (artifact=$ROOTFS profile=$PROFILE)"
