#!/usr/bin/env bash
# Run inside WSL (Debian). Fixes CRLF on /mnt/e (sed -i fails on drvfs).
set -euo pipefail

python3 <<'PY'
from pathlib import Path
root = Path("/mnt/e/project-infi/wolf-cog-os/scripts")
for p in sorted(root.glob("*.sh")):
    if not p.is_file():
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        continue
    fixed = text.replace("\r\n", "\n").replace("\r", "\n")
    if fixed != text:
        p.write_text(fixed, encoding="utf-8")
        print("fixed", p.name)
PY

PAYLOAD_CACHE="${HOME}/.cogos-payload-cache"
PAYLOAD_REPO="/mnt/e/project-infi/wolf-cog-os/payload"
ISO_NAME="debian-live-13.5.0-amd64-cinnamon.iso"
DEBIAN_ISO="${COGOS_DEBIAN_ISO:-${HOME}/${ISO_NAME}}"
MIN_DEBIAN_BYTES=3000000000
BASE_ISO=""

validate_debian_iso() {
  local path="$1"
  local bytes
  bytes="$(stat -c%s "$path" 2>/dev/null || stat -f%z "$path")"
  if (( bytes < MIN_DEBIAN_BYTES )); then
    echo "ERROR: Debian ISO appears truncated (size=${bytes}). Delete and re-download." >&2
    echo "  rm -f '$path'" >&2
    echo "  Download on Windows (not WSL — TLS is unreliable for multi-GB):" >&2
    echo "    curl.exe -L -o C:\\Users\\randj\\Downloads\\${ISO_NAME} \\" >&2
    echo "      https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/${ISO_NAME}" >&2
    echo "  cp /mnt/c/Users/randj/Downloads/${ISO_NAME} ~/" >&2
    return 1
  fi
  return 0
}

# Prefer ISO downloaded on Windows (WSL TLS often fails on large files).
WIN_DL="/mnt/c/Users/randj/Downloads/${ISO_NAME}"
if [[ ! -f "$DEBIAN_ISO" && -f "$WIN_DL" ]]; then
  echo "Found Windows download: $WIN_DL — copying to $DEBIAN_ISO"
  cp -f "$WIN_DL" "$DEBIAN_ISO"
fi

if [[ -f "$DEBIAN_ISO" ]]; then
  validate_debian_iso "$DEBIAN_ISO"
  BASE_ISO="$DEBIAN_ISO"
fi

if [[ -z "$BASE_ISO" && "${COGOS_SKIP_DEBIAN_DOWNLOAD:-0}" != "1" ]]; then
  echo "Debian base ISO missing — trying download (set COGOS_SKIP_DEBIAN_DOWNLOAD=1 to skip)..."
  echo "NOTE: Large downloads from inside WSL often fail (TLS). Prefer Windows:" >&2
  echo "  curl.exe -L -o C:\\Users\\randj\\Downloads\\${ISO_NAME} \\" >&2
  echo "    https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/${ISO_NAME}" >&2
  bash /mnt/e/project-infi/wolf-cog-os/scripts/download-debian-live-iso.sh "$DEBIAN_ISO"
  validate_debian_iso "$DEBIAN_ISO"
  BASE_ISO="$DEBIAN_ISO"
fi

if [[ -z "$BASE_ISO" && "${COGOS_SKIP_DEBIAN_DOWNLOAD:-0}" == "1" && -n "${COGOS_DEBIAN_ISO:-}" ]]; then
  echo "ERROR: COGOS_DEBIAN_ISO set but missing or invalid: $DEBIAN_ISO" >&2
  exit 1
fi

if [[ -z "$BASE_ISO" ]]; then
  for candidate in \
    "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" \
    "/mnt/e/project-infi/wolf-cog-os/output/wolf-cog-os-12.22.0-wolf-os.iso"; do
    if [[ -f "$candidate" ]]; then
      BASE_ISO="$candidate"
      echo "Using existing ISO as build substrate: $BASE_ISO"
      break
    fi
  done
fi

if [[ -z "$BASE_ISO" ]]; then
  echo "ERROR: no Debian or fallback ISO found. Place ${ISO_NAME} in ~/" >&2
  exit 1
fi

if [[ ! -f "$PAYLOAD_CACHE/opt/cogos/config/release_manifest.json" ]]; then
  echo "Payload cache incomplete — restoring from metal workdir..."
  bash /mnt/e/project-infi/wolf-cog-os/scripts/restore-payload-cache.sh
fi

if [[ -d "$PAYLOAD_REPO/opt/cogos" ]]; then
  echo "Overlaying repo payload onto cache (no delete): $PAYLOAD_REPO"
  rsync -a \
    --exclude 'opt/cogos/memory/' \
    --exclude '**/__pycache__/' \
    --exclude '*.pyc' \
    "$PAYLOAD_REPO/" "$PAYLOAD_CACHE/"
fi
echo "Using payload cache: $PAYLOAD_CACHE"
echo "Build substrate: $BASE_ISO"

export COGOS_PAYLOAD="$PAYLOAD_CACHE"
export COGOS_PAYLOAD="$PAYLOAD_CACHE"
export COGOS_SURPRISE_WORK="${COGOS_SURPRISE_WORK:-${HOME}/.cogos-surprise-work-${COGOS_TAG:-daily-driver-1.6-surprise}}"
bash /mnt/e/project-infi/wolf-cog-os/scripts/verify-surprise-release.sh

if [[ -d "$COGOS_SURPRISE_WORK" ]]; then
  STALE="${COGOS_SURPRISE_WORK}.stale-$(date +%s)"
  echo "Moving previous workdir aside -> $STALE"
  mv "$COGOS_SURPRISE_WORK" "$STALE" 2>/dev/null || rm -rf "$COGOS_SURPRISE_WORK" || true
fi
cd /mnt/e/project-infi/wolf-cog-os
export COGOS_PAYLOAD="$PAYLOAD_CACHE"
export COGOS_OUT="${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso"

echo ""
echo "=== Building release surprise ISO (Calamares hook + first-boot fix) ==="
echo "Log: /tmp/cogos-surprise-build.log"
echo ""

bash scripts/build-surprise-installer.sh "$BASE_ISO" \
  2>&1 | tee /tmp/cogos-surprise-build.log

echo ""
echo "=== Done. Log: /tmp/cogos-surprise-build.log ==="
ls -lh "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso.sha256" 2>/dev/null
if [[ -f "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" ]]; then
  cp -f "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso" "${HOME}/Wolf-CoG-OS-daily-driver-surprise.iso.sha256" \
    /mnt/e/project-infi/ 2>/dev/null || true
  ls -lh /mnt/e/project-infi/Wolf-CoG-OS-daily-driver-surprise.iso 2>/dev/null || true
fi
