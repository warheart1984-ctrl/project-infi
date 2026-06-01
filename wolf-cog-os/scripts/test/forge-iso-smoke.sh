#!/usr/bin/env bash
# Forge ISO contract smoke checks for CI and local validation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
ROOTFS=""
ISO=""

usage() {
  cat <<USAGE
Usage:
  bash wolf-cog-os/scripts/test/forge-iso-smoke.sh [--rootfs PATH] [--iso PATH]

Checks:
  - Forge GRUB template markers
  - Optional staged /forge layout inside rootfs
  - Optional built ISO presence
USAGE
}

while (($# > 0)); do
  case "$1" in
    --rootfs)
      ROOTFS="$2"
      shift 2
      ;;
    --iso)
      ISO="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"
bash wolf-cog-os/scripts/test/test-forge-grub.sh

if [[ -n "$ROOTFS" ]]; then
  if [[ ! -d "$ROOTFS" ]]; then
    echo "ERROR: rootfs path not found: $ROOTFS" >&2
    exit 3
  fi
  for required in \
    forge/pipelines/minimal.yaml \
    forge/scripts/forge-menu.sh \
    forge/scripts/forge-run-pipeline.sh \
    forge/README.md \
    usr/local/bin/forge-menu \
    usr/local/bin/forge-run-pipeline; do
    if [[ ! -e "$ROOTFS/$required" ]]; then
      echo "ERROR: missing staged forge path in rootfs: $required" >&2
      exit 4
    fi
  done
  echo "forge rootfs layout smoke: pass ($ROOTFS)"
fi

if [[ -n "$ISO" ]]; then
  if [[ ! -f "$ISO" ]]; then
    echo "ERROR: ISO not found: $ISO" >&2
    exit 5
  fi
  size="$(stat -c%s "$ISO" 2>/dev/null || stat -f%z "$ISO")"
  if (( size < 1000000 )); then
    echo "ERROR: ISO too small (${size} bytes): $ISO" >&2
    exit 6
  fi
  if command -v python3 >/dev/null 2>&1 && [[ -f "$ROOT_DIR/wolf-cog-os/scripts/validate-substrate.py" ]]; then
    python3 "$ROOT_DIR/wolf-cog-os/scripts/validate-substrate.py" \
      --iso "$ISO" \
      --substrate-id "${COGOS_SUBSTRATE_ID:-auto}" \
      --mode "${COGOS_SUBSTRATE_VALIDATION_MODE:-fail}"
  fi
  echo "forge ISO presence smoke: pass ($ISO, ${size} bytes)"
fi

echo "forge ISO contract smoke: pass"
