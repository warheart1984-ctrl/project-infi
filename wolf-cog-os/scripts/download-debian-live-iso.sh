#!/usr/bin/env bash
# Download Debian live cinnamon ISO if missing (for surprise release build).
set -euo pipefail

ISO_NAME="debian-live-13.5.0-amd64-cinnamon.iso"
MIN_BYTES=3000000000

if [[ -n "${1:-}" ]]; then
  if [[ "$1" == */* ]]; then
    DEST="$1"
    ISO_NAME="$(basename "$1")"
  else
    ISO_NAME="$1"
    DEST="${COGOS_DEBIAN_ISO:-${HOME}/${ISO_NAME}}"
  fi
else
  DEST="${COGOS_DEBIAN_ISO:-${HOME}/${ISO_NAME}}"
fi
URL="${COGOS_DEBIAN_ISO_URL:-https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/${ISO_NAME}}"
TMP="${DEST}.partial"

validate_iso_size() {
  local path="$1"
  local label="${2:-ISO}"
  local bytes
  bytes="$(stat -c%s "$path" 2>/dev/null || stat -f%z "$path")"
  if (( bytes < MIN_BYTES )); then
    echo "ERROR: ${label} appears truncated (size=${bytes} bytes, need >= ${MIN_BYTES})." >&2
    echo "       Delete and re-download: rm -f '$path'" >&2
    return 1
  fi
  return 0
}

if [[ -f "$DEST" ]]; then
  if validate_iso_size "$DEST" "Debian live ISO"; then
    echo "Debian live ISO already present: $DEST"
    ls -lh "$DEST"
    exit 0
  fi
  rm -f "$DEST"
fi

echo "Downloading Debian live ISO (~4 GB)..."
echo "  URL:  $URL"
echo "  Dest: $DEST"
echo ""
echo "WARNING: Do not download multi-GB ISOs inside WSL (TLS often fails)."
echo "  Use Windows instead, then copy into WSL:"
echo "    curl.exe -L -o C:\\Users\\randj\\Downloads\\${ISO_NAME} \"$URL\""
echo "    cp /mnt/c/Users/randj/Downloads/${ISO_NAME} ~/"
echo ""
mkdir -p "$(dirname "$DEST")"
# Keep existing .partial for resume; only remove stale final file (handled above).

download_ok=0
if command -v wget >/dev/null 2>&1; then
  wget --tries=0 --retry-connrefused --read-timeout=30 --timeout=30 -c "$URL" -O "$TMP"
  download_ok=1
elif command -v curl >/dev/null 2>&1; then
  curl -fL -C - "$URL" -o "$TMP"
  download_ok=1
else
  echo "Using python3 to download (install wget for resume support)..."
  python3 <<PY
import sys
import urllib.request
from pathlib import Path

url = "$URL"
dest = Path(r"$TMP")
dest.parent.mkdir(parents=True, exist_ok=True)
print("Fetching", url)
try:
    urllib.request.urlretrieve(url, dest)
except Exception as e:
    print(f"Download failed: {e}", file=sys.stderr)
    sys.exit(1)
print("Saved", dest, dest.stat().st_size, "bytes")
PY
  download_ok=1
fi

if (( download_ok != 1 )); then
  rm -f "$TMP"
  echo "ERROR: download failed" >&2
  exit 1
fi

if ! validate_iso_size "$TMP" "Downloaded Debian live ISO"; then
  rm -f "$TMP"
  exit 1
fi

mv "$TMP" "$DEST"
ls -lh "$DEST"
echo "Download complete."
