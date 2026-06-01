#!/usr/bin/env bash
# Resume Wolf CoG OS full ISO build from existing WSL workdir (skip extract/unsquashfs).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO="${1:-${HOME}/debian-live-13.5.0-amd64-cinnamon.iso}"

export COGOS_WORK="${COGOS_WORK:-${HOME}/.cogos-universal-installer-work}"
export COGOS_RESUME_WORK=1
export TMPDIR="${TMPDIR:-${COGOS_WORK}/tmp}"
mkdir -p "$TMPDIR"

echo "=== Resume Wolf CoG OS build ==="
echo "Work:   $COGOS_WORK"
echo "ISO:    $ISO"
echo "Log:    /tmp/wolf-cog-os-full-build.log"
echo ""

exec bash "$SCRIPT_DIR/build-wolf-cog-os-full.sh" "$ISO" 2>&1 | tee /tmp/wolf-cog-os-full-build.log
