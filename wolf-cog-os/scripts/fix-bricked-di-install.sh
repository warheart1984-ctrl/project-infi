#!/usr/bin/env bash
# Unbrick a d-i install: restore native systemd PID1 + enable cogos-runtime.service.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-bricked-di-install.sh /dev/sdXN"
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Unbricking Wolf CoG OS install on $MNT ..."

# Restore native systemd as PID1
rm -f "$MNT/usr/sbin/init" "$MNT/sbin/init"
ln -sf /lib/systemd/systemd "$MNT/usr/sbin/init"
if [[ -d "$MNT/sbin" ]]; then
  ln -sf /lib/systemd/systemd "$MNT/sbin/init"
fi
echo "  PID1 -> /lib/systemd/systemd"

# shellcheck source=lib/cogos-systemd-stack.sh
source "$SCRIPT_DIR/lib/cogos-systemd-stack.sh"

PAYLOAD="$SCRIPT_DIR/../payload"
for rel in "${COGOS_BOOT_STACK_UNITS[@]}"; do
  f="${rel#etc/systemd/system/}"
  [[ -f "$PAYLOAD/etc/systemd/system/$f" ]] || continue
  install_cogos_boot_stack_file "$PAYLOAD" "$MNT" "$rel"
  echo "  installed $rel"
done

find "$MNT/etc/systemd/system" \( -name '*.service' -o -name '*.conf' \) -type f \
  -exec chmod 644 {} + 2>/dev/null || true

# Remove SysV hooks that break systemd first boot
rm -f "$MNT/etc/init.d/90cogos" 2>/dev/null || true
for rc_dir in "$MNT"/etc/rc*.d; do
  [[ -d "$rc_dir" ]] || continue
  rm -f "$rc_dir"/[SK]??cogos "$rc_dir"/[SK]??90cogos 2>/dev/null || true
done
rm -f "$MNT/etc/systemd/system/90cogos.service" \
      "$MNT/etc/systemd/system/multi-user.target.wants/90cogos.service" 2>/dev/null || true

if [[ -f "$PAYLOAD/usr/local/bin/cogos-install-finish" ]]; then
  install -D -m755 "$PAYLOAD/usr/local/bin/cogos-install-finish" "$MNT/usr/local/bin/cogos-install-finish"
fi
for launcher in firstboot.sh governance-grace.sh governance-daemon spine observer; do
  [[ -f "$PAYLOAD/usr/lib/cogos/$launcher" ]] || continue
  install -D -m755 "$PAYLOAD/usr/lib/cogos/$launcher" "$MNT/usr/lib/cogos/$launcher"
done

if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1 --quiet
fi

if chroot "$MNT" command -v update-initramfs >/dev/null 2>&1; then
  chroot "$MNT" update-initramfs -u -k all || true
fi
if chroot "$MNT" command -v update-grub >/dev/null 2>&1; then
  chroot "$MNT" update-grub || true
fi

echo "Done. Reboot from internal disk (remove USB)."
echo "Then: systemctl status cogos-firstboot.service cogos-governance.service cogos-spine.service cogos-observer.service"
