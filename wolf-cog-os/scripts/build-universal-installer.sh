#!/usr/bin/env bash
# Wolf CoG OS — Regular edition with full runtime (Debian-like installer UX)
#
# One bootable ISO:
# - Live boot: systemd PID1 + pre-pack integrity gate
# - Install: stock Debian gtk d-i + preseed late_command (full runtime on disk)
#   Fallback: cogos-install apply from live terminal
#
# Usage:
#   bash wolf-cog-os/scripts/build-universal-installer.sh [debian-live.iso]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/update-full-runtime-manifest.sh
source "$SCRIPT_DIR/lib/update-full-runtime-manifest.sh"
# shellcheck source=lib/ensure-payload-ready.sh
source "$SCRIPT_DIR/lib/ensure-payload-ready.sh"
# shellcheck source=stage-nova-cortex-into-payload.sh
source "$SCRIPT_DIR/stage-nova-cortex-into-payload.sh"

TAG="${COGOS_TAG:-wolf-cog-os-full-3.5}"
BUILD_DATE="${COGOS_BUILD_DATE:-$(date -u +%Y-%m-%d)}"
export COGOS_TAG="$TAG"
export COGOS_BUILD_DATE="$BUILD_DATE"
export COGOS_PAYLOAD_SEED_FROM_SURPRISE="${COGOS_PAYLOAD_SEED_FROM_SURPRISE:-1}"
export COGOS_KEEP_SYSTEMD_PID1="${COGOS_KEEP_SYSTEMD_PID1:-1}"
export COGOS_SURPRISE_WORK="${COGOS_SURPRISE_WORK:-${HOME}/.cogos-surprise-work-daily-driver-1.6-surprise}"
export COGOS_ENABLE_PID1=0
export COGOS_METAL_INSTALL=1
export COGOS_STEALTH_INSTALL=0
export COGOS_SURPRISE_INSTALL=0
export COGOS_DI_INSTALL=1
export COGOS_GRAPHICAL_INSTALL=0
export COGOS_FULL_RUNTIME=1
export COGOS_GRUB_MERGE=1
export COGOS_BOOT_PROFILE=debian
export COGOS_LIVE_FINDISO=0
export COGOS_PLYMOUTH_POLICY="${COGOS_PLYMOUTH_POLICY:-optional}"
export COGOS_SQUASHFS_COMP="${COGOS_SQUASHFS_COMP:-xz}"
export COGOS_WORK="${COGOS_UNIVERSAL_WORK:-${HOME}/.cogos-universal-installer-work}"

BASE_ISO="${1:-${COGOS_DEBIAN_ISO:-$DEBIAN_BASE_ISO}}"
if [[ ! -f "$BASE_ISO" && -f "${HOME}/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
  BASE_ISO="${HOME}/debian-live-13.5.0-amd64-cinnamon.iso"
fi
if [[ ! -f "$BASE_ISO" && -f "/mnt/e/project-infi/debian-live-13.5.0-amd64-cinnamon.iso" ]]; then
  BASE_ISO="/mnt/e/project-infi/debian-live-13.5.0-amd64-cinnamon.iso"
fi

if [[ ! -f "$BASE_ISO" ]]; then
  echo "ERROR: Debian live ISO not found: $BASE_ISO" >&2
  echo "Place debian-live-13.5.0-amd64-cinnamon.iso in repo root or pass path as arg." >&2
  exit 3
fi

export COGOS_BOOT_REPLAY_ISO="${COGOS_BOOT_REPLAY_ISO:-$BASE_ISO}"

COGOS_OUT_FINAL="${COGOS_OUT:-$REPO_ROOT/Wolf-CoG-OS-full.iso}"
if [[ "$COGOS_OUT_FINAL" == /mnt/* ]]; then
  export COGOS_OUT="${HOME}/Wolf-CoG-OS-full.iso"
else
  export COGOS_OUT="$COGOS_OUT_FINAL"
fi

if [[ "$(df -T "$COGOS_WORK" 2>/dev/null | tail -1 | awk '{print $2}')" == "9p" ]]; then
  echo "ERROR: COGOS_WORK on Windows mount (9p) breaks unsquashfs symlinks." >&2
  exit 4
fi

PAYLOAD_CACHE="${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}"
ensure_payload_ready "$WOLF_COGOS_ROOT/payload" "$PAYLOAD_CACHE"
stage_nova_cortex_into_payload "$PAYLOAD_CACHE" "$WOLF_COGOS_ROOT/payload"

MANIFEST_ROOT="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}/opt/cogos"
update_full_runtime_manifest "$MANIFEST_ROOT" "$TAG" "$BUILD_DATE" "debian"

echo "=== Wolf CoG OS — Unified Full Runtime (Nova Cortex + gtk installer) ==="
echo "Tag:        $COGOS_TAG"
echo "Substrate:  $BASE_ISO"
echo "Live boot:  systemd PID1 + pre-pack integrity gate"
echo "Runtime:    boot stack (firstboot → governance → spine → observer)"
echo "PID1:       keep native systemd on disk (COGOS_KEEP_SYSTEMD_PID1=1)"
echo "Nova:       Nova Cortex v3 unified (cog_runtime + bridge staged on ISO)"
echo "Live:       Wolf CoG OS branding + desktop Install Wolf CoG OS icon"
echo "Install:    Start Wolf CoG OS installer (gtk d-i from /install/gtk/)"
echo "Fallback:   cogos-install apply from live terminal"
echo "Output:     $COGOS_OUT"
echo "Payload:    ${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
echo "Boot replay:$COGOS_BOOT_REPLAY_ISO"
echo "Plymouth:   $COGOS_PLYMOUTH_POLICY"

bash "$SCRIPT_DIR/verify-full-runtime-release.sh" || exit 5
bash "$SCRIPT_DIR/preflight-debian-live-installer.sh" "$BASE_ISO" "$COGOS_BOOT_REPLAY_ISO"
bash "$SCRIPT_DIR/preflight-universal-installer.sh" "$BASE_ISO" "$COGOS_BOOT_REPLAY_ISO"

bash "$SCRIPT_DIR/build.sh" "$BASE_ISO"

if [[ "$COGOS_OUT" != "$COGOS_OUT_FINAL" ]]; then
  cp -f "$COGOS_OUT" "${COGOS_OUT}.sha256" "$COGOS_OUT_FINAL" "${COGOS_OUT_FINAL}.sha256" 2>/dev/null || \
    echo "WARN: copy to $COGOS_OUT_FINAL failed — use $COGOS_OUT" >&2
fi

echo ""
echo "=== Wolf CoG OS full runtime ISO complete ==="
echo "Flash: Rufus DD mode (recommended) or Ventoy"
echo "Boot:  Start Wolf CoG OS installer (default)  OR  Live (full runtime + desktop install icon)"
echo "Install: stock Debian gtk graphical installer + Wolf runtime hook on finish"
echo "Terminal install:  submenu Terminal install, then cogos-install apply"
echo "Proof: \$COGOS_WORK/proof/live-boot-integrity/validation.json"
echo "Proof: \$COGOS_WORK/proof/di-initrd-wifi/summary.txt"
echo "Metal:  wolf-cog-os/docs/METAL_PROOF_CHECKLIST.md"
echo "SHA:   ${COGOS_OUT}.sha256"
ls -lh "$COGOS_OUT" "${COGOS_OUT}.sha256" 2>/dev/null || true
