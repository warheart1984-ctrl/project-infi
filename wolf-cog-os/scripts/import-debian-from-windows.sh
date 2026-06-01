#!/usr/bin/env bash
# Import Debian live ISO downloaded on Windows (browser / PowerShell / curl.exe).
# WSL TLS is unreliable for multi-GB downloads — always fetch on Windows first.
set -euo pipefail

ISO_NAME="debian-live-13.5.0-amd64-cinnamon.iso"
MIN_BYTES=3000000000
WIN_DL="${COGOS_WINDOWS_DEBIAN_ISO:-}"
if [[ -z "$WIN_DL" ]]; then
  for candidate in \
    "/mnt/c/Users/randj/Downloads/${ISO_NAME}" \
    "/mnt/c/Users/randj/Downloads/${ISO_NAME%.iso} (1).iso"; do
    if [[ -f "$candidate" ]]; then
      WIN_DL="$candidate"
      break
    fi
  done
  if [[ -z "$WIN_DL" ]]; then
    best=""
    best_bytes=0
    for candidate in /mnt/c/Users/randj/Downloads/debian-live-*-cinnamon*.iso; do
      [[ -f "$candidate" ]] || continue
      bytes="$(stat -c%s "$candidate" 2>/dev/null || stat -f%z "$candidate")"
      if (( bytes > best_bytes )); then
        best="$candidate"
        best_bytes="$bytes"
      fi
    done
    WIN_DL="$best"
  fi
fi
DEST="${COGOS_DEBIAN_ISO:-${HOME}/${ISO_NAME}}"

if [[ ! -f "$WIN_DL" ]]; then
  echo "ERROR: ISO not found at $WIN_DL" >&2
  echo "Download on Windows (not WSL):" >&2
  echo "  curl.exe -L -o C:\\Users\\randj\\Downloads\\${ISO_NAME} \\" >&2
  echo "    https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/${ISO_NAME}" >&2
  exit 1
fi

bytes="$(stat -c%s "$WIN_DL" 2>/dev/null || stat -f%z "$WIN_DL")"
if (( bytes < MIN_BYTES )); then
  echo "ERROR: Windows ISO appears truncated (${bytes} bytes). Re-download in browser." >&2
  exit 1
fi

echo "Importing $WIN_DL -> $DEST"
rm -f "${DEST}.partial"
cp -f "$WIN_DL" "$DEST"
ls -lh "$DEST"

export COGOS_DEBIAN_ISO="$DEST"
export COGOS_SKIP_DEBIAN_DOWNLOAD=1
exec bash /mnt/e/project-infi/wolf-cog-os/scripts/fix-and-build-surprise.sh
