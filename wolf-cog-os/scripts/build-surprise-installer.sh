#!/usr/bin/env bash
# Wolf CoG OS — Surprise Daily Driver ISO
#
# Looks like stock Debian live + normal installer (Ventoy or Rufus).
# CoGOS payload is embedded silently; install finish enables PID1 on disk.
# First reboot from hard drive: full Wolf CoG OS + SuperNova daily driver takeover.
#
# Usage:
#   bash wolf-cog-os/scripts/build-surprise-installer.sh [debian-live.iso]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

TAG="${COGOS_TAG:-daily-driver-1.6-surprise}"
BUILD_DATE="${COGOS_BUILD_DATE:-$(date -u +%Y-%m-%d)}"
export COGOS_TAG="$TAG"
export COGOS_BUILD_DATE="$BUILD_DATE"
export COGOS_ENABLE_PID1=0
export COGOS_STEALTH_INSTALL=1
export COGOS_SURPRISE_INSTALL=1
export COGOS_DAILY_DRIVER_PACKAGES="${COGOS_DAILY_DRIVER_PACKAGES:-0}"
export COGOS_BUILD_FROM_TREE="${COGOS_BUILD_FROM_TREE:-0}"
export COGOS_GRUB_MERGE=1
export COGOS_BOOT_PROFILE=surprise
export COGOS_LIVE_FINDISO=0
export COGOS_SQUASHFS_COMP="${COGOS_SQUASHFS_COMP:-xz}"
export COGOS_WORK="${COGOS_SURPRISE_WORK:-${HOME}/.cogos-surprise-work}"

COGOS_OUT_FINAL="${COGOS_OUT:-$REPO_ROOT/Wolf-CoG-OS-daily-driver-surprise.iso}"
if [[ "$COGOS_OUT_FINAL" == /mnt/* ]]; then
  export COGOS_OUT="${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso"
else
  export COGOS_OUT="$COGOS_OUT_FINAL"
fi

ISO_FOR_BUILD="${1:-$DEBIAN_BASE_ISO}"
if [[ ! -f "$ISO_FOR_BUILD" ]]; then
  echo "ERROR: Debian live ISO not found: $ISO_FOR_BUILD" >&2
  echo "Download debian-live-13.5.0-amd64-cinnamon.iso to repo root or wolf-cog-os/sources/" >&2
  echo "  https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/" >&2
  exit 3
fi

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK on Windows mount (9p) breaks unsquashfs symlinks." >&2
  exit 4
fi

echo "=== Wolf CoG OS Surprise Daily Driver ISO ==="
echo "Tag:        $COGOS_TAG"
echo "Substrate:  $ISO_FOR_BUILD"
echo "Live UX:    stock Debian (stealth)"
echo "Disk boot:  CoGOS PID1 + SuperNova + full daily driver"
echo "Output:     $COGOS_OUT"
echo "Work:       $COGOS_WORK"
echo "Packages:   COGOS_DAILY_DRIVER_PACKAGES=${COGOS_DAILY_DRIVER_PACKAGES}"
echo "Rootfs src: COGOS_BUILD_FROM_TREE=${COGOS_BUILD_FROM_TREE}"
if [[ "${COGOS_BUILD_FROM_TREE}" == "1" ]]; then
  echo "Rootfs dir: ${COGOS_ROOTFS_SRC:-$WOLF_ROOTFS_OUT}"
fi
if [[ -z "${COGOS_PAYLOAD:-}" && -f "${HOME}/.cogos-payload-cache/opt/cogos/config/release_manifest.json" ]]; then
  export COGOS_PAYLOAD="${HOME}/.cogos-payload-cache"
fi
if [[ -n "${COGOS_PAYLOAD:-}" ]]; then
  echo "Payload:    $COGOS_PAYLOAD"
fi

MANIFEST_ROOT="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}/opt/cogos"
python3 <<PY
import json
from pathlib import Path

root = Path(r"$MANIFEST_ROOT")
manifest = json.loads((root / "config/release_manifest.json").read_text(encoding="utf-8-sig"))
manifest["version"] = "$TAG"
manifest["build_date"] = "$BUILD_DATE"
manifest["release_name"] = "Wolf CoG OS Daily Driver (surprise install)"
components = manifest.setdefault("components", {})
components["surprise_installer"] = "debian_stealth_pid1_on_disk_v1"
components["boot_profile"] = "surprise"
components["daily_driver"] = "full_nova_stack_v1"
components["install_hook"] = "cogos-install-finish"
components["calamares_hook"] = "shellprocess@cogos-finish"
(root / "config/release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print("release_manifest.json updated for surprise daily driver")
PY

if [[ "${COGOS_BUILD_FROM_TREE}" == "1" && "${COGOS_BUILD_ROOTFS_FIRST:-0}" == "1" ]]; then
  echo "Building native rootfs tree before ISO assembly..."
  COGOS_ENABLE_PID1="${COGOS_ROOTFS_PID1:-1}" bash "$SCRIPT_DIR/build-rootfs.sh"
fi

bash scripts/verify-surprise-release.sh || exit 5

bash "$SCRIPT_DIR/build.sh" "$ISO_FOR_BUILD"

if [[ "$COGOS_OUT" != "$COGOS_OUT_FINAL" ]]; then
  cp -f "$COGOS_OUT" "${COGOS_OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $COGOS_OUT" >&2
fi

echo ""
echo "=== Surprise Daily Driver ISO complete ==="
echo "Flash: Ventoy (copy ISO) or Rufus DD / ISO mode"
echo "Boot:  normal Debian live → Install Debian (graphical)"
echo "After install: reboot from internal disk → Wolf CoG OS + Nova takeover"
echo "SHA:   ${COGOS_OUT}.sha256"
ls -lh "$COGOS_OUT" "${COGOS_OUT}.sha256" 2>/dev/null || true
