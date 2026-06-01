#!/usr/bin/env bash
# Fix a disk install that stalls on first reboot (run from Debian live USB).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-stalled-disk-boot.sh /dev/sdXN"
  echo "  Mount your installed root partition (ext4), not EFI unless combined."
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Fixing CoGOS boot on $MNT ..."

# Option A: restore normal Debian init (boots immediately)
if [[ "${COGOS_FIX_MODE:-fast}" == "debian" ]]; then
  rm -f "$MNT/usr/sbin/init" "$MNT/sbin/init" 2>/dev/null || true
  ln -sf /lib/systemd/systemd "$MNT/usr/sbin/init"
  echo "Restored init -> systemd. Reboot from internal disk."
  exit 0
fi

# Option B: enable CoGOS correctly + fast-first-boot markers
if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target
else
  echo "WARN: cogos-install-finish missing; restoring systemd init" >&2
  rm -f "$MNT/usr/sbin/init" 2>/dev/null || true
  ln -sf /lib/systemd/systemd "$MNT/usr/sbin/init"
fi

# Safe kernel param for one boot (edit GRUB)
if [[ -f "$MNT/etc/default/grub" ]]; then
  if ! grep -q 'cogos.safe=1' "$MNT/etc/default/grub"; then
    sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="cogos.safe=1 /' \
      "$MNT/etc/default/grub" 2>/dev/null || true
  fi
  if chroot "$MNT" command -v update-grub >/dev/null 2>&1; then
    chroot "$MNT" update-grub
  fi
fi

echo "Done. Remove USB and reboot from internal disk (not the installer USB)."
echo ""
echo "If it still stalls:"
echo "  1. Boot the live USB again"
echo "  2. sudo bash wolf-cog-os/scripts/fix-stalled-disk-boot.sh /dev/sdXN"
echo "  3. Or emergency bypass: edit GRUB, add cogos.safe=1 to the linux line"
echo ""
echo "Logs after boot: /var/log/cogos-install-finish.log /var/log/cogos-first-boot.log /var/log/cogos-pid1.log"
