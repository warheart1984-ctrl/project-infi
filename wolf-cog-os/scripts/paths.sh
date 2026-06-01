#!/usr/bin/env bash
# Canonical Wolf CoG OS path layout — source this from every build script.
set -euo pipefail

_wolf_paths_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export WOLF_COGOS_ROOT="$(cd "$_wolf_paths_dir/.." && pwd)"
export REPO_ROOT="$(cd "$WOLF_COGOS_ROOT/.." && pwd)"

export WOLF_PAYLOAD="${COGOS_PAYLOAD:-$WOLF_COGOS_ROOT/payload}"
export WOLF_BRANDING="${COGOS_BRANDING:-$WOLF_COGOS_ROOT/branding}"
export WOLF_OUTPUT="${COGOS_OUTPUT_DIR:-$WOLF_COGOS_ROOT/output}"
export WOLF_SOURCES="${COGOS_SOURCES_DIR:-$WOLF_COGOS_ROOT/sources}"
export WOLF_CONFIG="${COGOS_CONFIG_DIR:-$WOLF_COGOS_ROOT/config}"
export WOLF_PACKAGE_CONFIG="${COGOS_PACKAGE_CONFIG_DIR:-$WOLF_CONFIG/packages}"

export COGOS_ROOT="${COGOS_ROOT:-$WOLF_PAYLOAD/opt/cogos}"
export COGOS_TAG="${COGOS_TAG:-12.22.0-wolf-os}"
export COGOS_WORK="${COGOS_WORK:-/tmp/wolf-cog-os-build-${COGOS_TAG//[^A-Za-z0-9]/-}}"
export WOLF_ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$WOLF_COGOS_ROOT/build/rootfs-${COGOS_TAG//[^A-Za-z0-9]/-}}"
export COGOS_ROOTFS_SRC="${COGOS_ROOTFS_SRC:-$WOLF_ROOTFS_OUT}"
export WOLF_PACKAGE_BASE="${COGOS_BASE_PACKAGES_FILE:-$WOLF_PACKAGE_CONFIG/base.txt}"
export WOLF_PACKAGE_DAILY="${COGOS_DAILY_PACKAGES_FILE:-$WOLF_PACKAGE_CONFIG/daily-driver.txt}"
export WOLF_PACKAGE_FORGE="${COGOS_FORGE_PACKAGES_FILE:-$WOLF_PACKAGE_CONFIG/forge.txt}"
export WOLF_FORGE_STAGING="${COGOS_FORGE_STAGING:-$WOLF_COGOS_ROOT/forge}"
export COGOS_SUBSTRATE_ISO="${COGOS_SUBSTRATE_ISO:-${COGOS_BOOT_REPLAY_ISO:-${COGOS_DEBIAN_ISO:-}}}"
export COGOS_SUBSTRATE_REGISTRY="${COGOS_SUBSTRATE_REGISTRY:-$WOLF_FORGE_STAGING/substrates/registry.json}"
export COGOS_ROOTFS_BACKEND="${COGOS_ROOTFS_BACKEND:-debootstrap}"
export COGOS_ROOTFS_BACKEND_REGISTRY="${COGOS_ROOTFS_BACKEND_REGISTRY:-$WOLF_FORGE_STAGING/backends/registry.json}"

# Default base images (place ISOs in repo root or wolf-cog-os/sources/)
DEBIAN_LIVE_ISO_NAME="debian-live-13.5.0-amd64-cinnamon.iso"
export DEBIAN_BASE_ISO="${COGOS_DEBIAN_ISO:-${1:-$REPO_ROOT/$DEBIAN_LIVE_ISO_NAME}}"
if [[ ! -f "$DEBIAN_BASE_ISO" && -f "$WOLF_SOURCES/$DEBIAN_LIVE_ISO_NAME" ]]; then
  DEBIAN_BASE_ISO="$WOLF_SOURCES/$DEBIAN_LIVE_ISO_NAME"
fi

export TRIXIE_BASE_ISO="${COGOS_TRIXIE_ISO:-${1:-$REPO_ROOT/TrixiePup64-Wayland-2601-260502.iso}}"
if [[ ! -f "$TRIXIE_BASE_ISO" && -f "$WOLF_SOURCES/TrixiePup64-Wayland-2601-260502.iso" ]]; then
  TRIXIE_BASE_ISO="$WOLF_SOURCES/TrixiePup64-Wayland-2601-260502.iso"
fi

wolf_iso_out() {
  local tag="${1:-$COGOS_TAG}"
  echo "${COGOS_OUT:-$WOLF_OUTPUT/wolf-cog-os-${tag}.iso}"
}

wolf_rootfs_out() {
  echo "${COGOS_ROOTFS_OUT:-$WOLF_ROOTFS_OUT}"
}

verify_iso_size() {
  local source_iso="$1"
  local output_iso="$2"
  local min_ratio="${COGOS_MIN_ISO_RATIO:-0.92}"
  local min_bytes="${COGOS_MIN_ISO_BYTES:-3400000000}"
  local src_size=0

  if [[ ! -f "$output_iso" ]]; then
    echo "ERROR: Output ISO missing: $output_iso" >&2
    return 10
  fi

  local out_size
  out_size="$(stat -c%s "$output_iso" 2>/dev/null || stat -f%z "$output_iso")"

  if [[ -f "$source_iso" ]]; then
    src_size="$(stat -c%s "$source_iso" 2>/dev/null || stat -f%z "$source_iso")"
    # Rocky/Fedora boot/install substrates (~1 GB) — not Debian live (~4 GB).
    if (( src_size < 2000000000 )); then
      min_ratio="${COGOS_MIN_ISO_RATIO:-0.35}"
      min_bytes=$(( src_size * 35 / 100 ))
      if (( min_bytes < 300000000 )); then
        min_bytes=300000000
      fi
    fi
  fi

  if (( out_size < min_bytes )); then
    echo "ERROR: Output ISO is too small ($(numfmt --to=iec "$out_size" 2>/dev/null || echo "${out_size} bytes"))." >&2
    echo "       Expected at least $(numfmt --to=iec "$min_bytes" 2>/dev/null || echo "${min_bytes} bytes")." >&2
    echo "       This usually means incomplete ISO extract, missing squashfs/install.img, or wrong base image." >&2
    return 10
  fi

  if (( src_size > 0 )); then
    local threshold
    threshold="$(python3 -c "print(int($src_size * $min_ratio))")"
    if (( out_size < threshold )); then
      pct="$(python3 -c "print(int((1 - float('${min_ratio}')) * 100))")"
      echo "ERROR: Output ISO ($(numfmt --to=iec "$out_size" 2>/dev/null || echo "$out_size"))" >&2
      echo "       is more than ${pct}% smaller than source ($(numfmt --to=iec "$src_size" 2>/dev/null || echo "$src_size"))." >&2
      echo "       Re-run with native Linux COGOS_WORK and xorriso extract (not partial bsdtar on /mnt)." >&2
      return 10
    fi
    echo "ISO size OK: output $(numfmt --to=iec "$out_size" 2>/dev/null || echo "$out_size") vs source $(numfmt --to=iec "$src_size" 2>/dev/null || echo "$src_size")"
  else
    echo "ISO size OK: output $(numfmt --to=iec "$out_size" 2>/dev/null || echo "$out_size") (source ISO not present for ratio check)"
  fi
}
