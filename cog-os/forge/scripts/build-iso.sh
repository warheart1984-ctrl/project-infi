#!/usr/bin/env bash
# Build Nova NorthStar CoG OS ISO tree and optional bootable ISO (xorriso replay).
set -euo pipefail

FORGE_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$FORGE_SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=../../scripts/lib/paths.sh
source "$REPO_ROOT/cog-os/scripts/lib/paths.sh"
# shellcheck source=lib/build-iso-packaging.sh
source "$FORGE_SCRIPT_DIR/lib/build-iso-packaging.sh"

PROFILE="${COG_PROFILE:-metal}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    -h|--help)
      cat <<EOF
usage: $0 [--profile metal|daily-driver|forge-selfhosted]

Builds:
  artifacts/cog-os/iso-tree-\$PROFILE/   (always)
  artifacts/cog-os/iso-work-\$PROFILE/   (squashfs + kernel/initrd when mksquashfs present)
  artifacts/cog-os/cog-os-\$PROFILE.iso  (when DEBIAN_BASE_ISO or COGOS_BOOT_REPLAY_ISO is set)

Environment:
  COGOS_SKIP_ISO=1          Skip xorriso even if substrate ISO is available
  DEBIAN_BASE_ISO           Debian live ISO for El Torito boot replay
  COGOS_BOOT_REPLAY_ISO     Alias for substrate ISO
EOF
      exit 0
      ;;
    *) echo "unknown: $1" >&2; exit 1 ;;
  esac
done

export COG_PROFILE="$PROFILE"
ROOTFS="$ARTIFACTS_DIR/rootfs-$PROFILE"
ISO_TREE="$ARTIFACTS_DIR/iso-tree-$PROFILE"
ISO_WORK="$ARTIFACTS_DIR/iso-work-$PROFILE"
ISO_OUT="$ARTIFACTS_DIR/cog-os-$PROFILE.iso"
REPLAY_ISO="${COGOS_BOOT_REPLAY_ISO:-${DEBIAN_BASE_ISO:-}}"

bash "$FORGE_SCRIPT_DIR/build-rootfs.sh" --profile "$PROFILE"

rm -rf "$ISO_TREE"
mkdir -p "$ISO_TREE/live"

cat >"$ISO_TREE/README.txt" <<EOF
Nova NorthStar CoG OS ISO tree (profile=$PROFILE)
Rootfs artifact: $ROOTFS
Squashfs work: $ISO_WORK/iso/live/
Bootable ISO: $ISO_OUT (requires DEBIAN_BASE_ISO for xorriso replay)
EOF

rsync -a "$ROOTFS/" "$ISO_TREE/live/rootfs/"

python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

out = Path(r"$ISO_TREE") / "profile-attestation.json"
out.write_text(json.dumps({
    "schema_version": "cog-os-profile-attestation.v1",
    "profile": "$PROFILE",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "iso_tree": str(out.parent),
    "rootfs": r"$ROOTFS",
}, indent=2) + "\n", encoding="utf-8")
print(out)
PY

stage_live_workdir "$ROOTFS" "$ISO_WORK"
echo "iso-tree ready: $ISO_TREE"
echo "iso-work ready: $ISO_WORK/iso/live/"

if [[ "${COGOS_SKIP_ISO:-0}" == "1" ]]; then
  echo "COGOS_SKIP_ISO=1 — skipping xorriso packaging"
  exit 0
fi

if [[ -z "$REPLAY_ISO" || ! -f "$REPLAY_ISO" ]]; then
  echo "No substrate ISO — set DEBIAN_BASE_ISO to produce $ISO_OUT"
  exit 0
fi

command -v xorriso >/dev/null 2>&1 || {
  echo "xorriso not found — squashfs work is ready; install xorriso to build $ISO_OUT" >&2
  exit 0
}

build_iso_from_workdir "$ISO_WORK" "$REPLAY_ISO" "$ISO_OUT"
echo "iso ready: $ISO_OUT"
