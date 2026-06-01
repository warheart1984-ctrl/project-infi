#!/usr/bin/env bash
# Diagnose why Wolf-CoG-OS-metal-fixed.iso boots reliably.
set -euo pipefail

SFS="${COGOS_METAL_SFS:-$HOME/metal-iso-extract/live/filesystem.squashfs}"
ROOT="${COGOS_METAL_INSPECT:-$HOME/metal-iso-rootfs-inspect}"
GRUB="${COGOS_METAL_GRUB:-$HOME/metal-iso-extract/boot/grub/grub.cfg}"

if [[ ! -f "$SFS" ]]; then
  echo "ERROR: squashfs not found: $SFS" >&2
  exit 1
fi

rm -rf "$ROOT"
mkdir -p "$ROOT"

paths=(
  etc/os-release
  usr/sbin/init
  usr/sbin/init.original
  sbin/init
  opt/cogos/bin/cognitive_init
  opt/cogos/config/boot_profile.json
  opt/cogos/config/boot_profile_daily_driver.json
  opt/cogos/config/release_manifest.json
  etc/calamares/settings.conf
  usr/local/bin/cogos-install-finish
  usr/local/bin/cogos-install
  usr/local/bin/cogos-first-boot
  etc/systemd/system/cogos-first-boot.service
)

for p in "${paths[@]}"; do
  unsquashfs -f -d "$ROOT" "$SFS" "$p" 2>/dev/null || true
done

echo "========== METAL ISO DIAGNOSIS =========="
echo ""
echo "--- GRUB (ISO top level) ---"
if [[ -f "$GRUB" ]]; then
  cat "$GRUB"
else
  echo "missing: $GRUB"
fi

echo ""
echo "--- init chain (squashfs) ---"
ls -la "$ROOT/usr/sbin/init" "$ROOT/sbin/init" 2>/dev/null || echo "no init symlinks"
if [[ -e "$ROOT/usr/sbin/init" ]]; then
  readlink -f "$ROOT/usr/sbin/init" 2>/dev/null || file "$ROOT/usr/sbin/init"
fi
if [[ -f "$ROOT/usr/sbin/init.original" ]]; then
  ls -la "$ROOT/usr/sbin/init.original"
fi

echo ""
echo "--- os-release ---"
cat "$ROOT/etc/os-release" 2>/dev/null || echo "missing"

echo ""
echo "--- boot_profile ---"
if [[ -f "$ROOT/opt/cogos/config/boot_profile.json" ]]; then
  python3 -m json.tool "$ROOT/opt/cogos/config/boot_profile.json" 2>/dev/null | head -50
else
  echo "missing"
fi

echo ""
echo "--- release_manifest (components) ---"
if [[ -f "$ROOT/opt/cogos/config/release_manifest.json" ]]; then
  python3 - <<PY
import json
from pathlib import Path
m = json.loads(Path("$ROOT/opt/cogos/config/release_manifest.json").read_text())
print("version:", m.get("version"))
print("components:", json.dumps(m.get("components", {}), indent=2))
PY
fi

echo ""
echo "--- Calamares hook ---"
if [[ -f "$ROOT/etc/calamares/settings.conf" ]]; then
  grep -nE 'shellprocess|cogos|umount|exec:' "$ROOT/etc/calamares/settings.conf" || echo "no cogos hook in calamares"
else
  echo "no calamares (live-only metal ISO)"
fi

echo ""
echo "--- install/first-boot scripts ---"
for f in cogos-install cogos-install-finish cogos-first-boot; do
  if [[ -x "$ROOT/usr/local/bin/$f" ]]; then
    echo "OK  /usr/local/bin/$f"
  else
    echo "MISS /usr/local/bin/$f"
  fi
done

echo ""
echo "--- cognitive_init first-boot handoff ---"
if [[ -f "$ROOT/opt/cogos/bin/cognitive_init" ]]; then
  grep -n 'FIRST_BOOT_PENDING\|cogos.safe\|handoff_native\|fail_closed' \
    "$ROOT/opt/cogos/bin/cognitive_init" | head -20
fi

echo ""
echo "--- squashfs size ---"
ls -lh "$SFS"
