#!/usr/bin/env bash
# Repair CoGOS daemons on an already-installed disk (boot live USB, run against root partition).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-installed-daemons.sh /dev/sdXN"
  echo "  Mounts ext4 root, installs missing daemon launcher + enables cogos-runtime.service"
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/../payload"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Repairing CoGOS daemons on $MNT ..."

PAYLOAD="$SCRIPT_DIR/../payload"

# Native systemd unit + launchers only (no SysV init.d)
for f in \
  usr/lib/cogos/firstboot.sh \
  usr/lib/cogos/governance-grace.sh \
  usr/lib/cogos/governance-daemon \
  usr/lib/cogos/spine \
  usr/lib/cogos/observer \
  usr/lib/cogos/boot-service-hardening.sh \
  etc/systemd/system/cogos-firstboot.service \
  etc/systemd/system/cogos-governance.service \
  etc/systemd/system/cogos-spine.service \
  etc/systemd/system/cogos-observer.service \
  etc/systemd/system/cogos-boot-hardening.service \
  etc/systemd/system/avahi-daemon.service.d/cogos-boot.conf \
  etc/systemd/system/blueman-mechanism.service.d/cogos-boot.conf \
  etc/systemd/system/udisks2.service.d/cogos-boot.conf; do
  if [[ -f "$PAYLOAD/$f" ]]; then
    if [[ "$f" == *.service ]]; then
      install -D -m644 "$PAYLOAD/$f" "$MNT/$f"
    else
      install -D -m755 "$PAYLOAD/$f" "$MNT/$f"
    fi
    echo "  installed $f"
  fi
done
find "$MNT/etc/systemd/system" \( -name '*.service' -o -name '*.conf' \) -type f -exec chmod 644 {} + 2>/dev/null || true
rm -f "$MNT/etc/init.d/90cogos" 2>/dev/null || true
for rc_dir in "$MNT"/etc/rc*.d; do
  [[ -d "$rc_dir" ]] || continue
  rm -f "$rc_dir"/[SK]??cogos "$rc_dir"/[SK]??90cogos 2>/dev/null || true
done

# Copy any missing cogos-* wrappers from payload cache / repo merged rootfs
if [[ -d "$PAYLOAD/usr/local/bin" ]]; then
  mkdir -p "$MNT/usr/local/bin"
  for bin in "$PAYLOAD"/usr/local/bin/cogos-*; do
    [[ -f "$bin" ]] || continue
    name="$(basename "$bin")"
    [[ -x "$MNT/usr/local/bin/$name" ]] && continue
    install -m755 "$bin" "$MNT/usr/local/bin/$name"
    echo "  installed $name"
  done
fi

# Re-run install finish to enable units + daily driver profile
if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1
else
  mkdir -p "$MNT/etc/systemd/system/multi-user.target.wants"
  ln -sf ../cogos-runtime.service "$MNT/etc/systemd/system/multi-user.target.wants/cogos-runtime.service"
fi

echo "Done. Reboot from internal disk."
echo "After boot: systemctl status cogos-governance.service cogos-spine.service cogos-observer.service"
echo "Logs: /var/log/cogos-firstboot.log /var/log/cogos-governance.log /var/log/cogos-spine.log /var/log/cogos-observer.log"
