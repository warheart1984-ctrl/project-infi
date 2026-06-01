#!/usr/bin/env bash
# Copy Wolf-CoG-OS-metal-fixed.iso to E: and extract; keep WSL original.
set -euo pipefail

ISO="${COGOS_METAL_ISO:-$HOME/Wolf-CoG-OS-metal-fixed.iso}"
DEST_ISO="${COGOS_METAL_ISO_COPY:-/mnt/e/project-infi/Wolf-CoG-OS-metal-fixed.iso}"
EXTRACT="${COGOS_METAL_EXTRACT:-$HOME/metal-iso-extract}"
EXTRACT_E="${COGOS_METAL_EXTRACT_E:-/mnt/e/project-infi/metal-iso-extract}"

if [[ ! -f "$ISO" ]]; then
  echo "ERROR: metal ISO not found: $ISO" >&2
  echo "Searched WSL home. Not on C:\\Users\\randj\\Downloads." >&2
  exit 1
fi

echo "=== Metal ISO source ==="
ls -lh "$ISO"
sha256sum "$ISO"

echo ""
echo "=== Copy to E: keeping WSL original ==="
if [[ -f "$DEST_ISO" ]]; then
  src_sum="$(sha256sum "$ISO" | awk '{print $1}')"
  dst_sum="$(sha256sum "$DEST_ISO" | awk '{print $1}')"
  if [[ "$src_sum" == "$dst_sum" ]]; then
    echo "E: copy already matches: $DEST_ISO"
  else
    cp -f "$ISO" "$DEST_ISO"
    echo "Updated E: copy"
  fi
else
  cp -f "$ISO" "$DEST_ISO"
  echo "Created E: copy"
fi
ls -lh "$ISO" "$DEST_ISO"

echo ""
echo "=== Extract to WSL ext4 ==="
rm -rf "$EXTRACT"
mkdir -p "$EXTRACT"
xorriso -osirrox on -indev "$ISO" -extract / "$EXTRACT"
file_count="$(find "$EXTRACT" -type f | wc -l)"
echo "Extracted $file_count files"
du -sh "$EXTRACT"

echo ""
echo "=== Mirror extract to E: ==="
rm -rf "$EXTRACT_E"
mkdir -p "$EXTRACT_E"
rsync -a "$EXTRACT/" "$EXTRACT_E/"
du -sh "$EXTRACT_E"

echo ""
echo "=== Done ==="
echo "ISO kept:  $ISO"
echo "ISO copy:  $DEST_ISO"
echo "Extract:   $EXTRACT"
echo "Extract E: $EXTRACT_E"
