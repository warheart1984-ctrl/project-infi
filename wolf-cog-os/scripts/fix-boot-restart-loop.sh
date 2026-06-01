#!/usr/bin/env bash
# Repair installed disk that stalls / reboot-loops on avahi, blueman, or udisks2.
# Run from Wolf CoG OS live USB:
#   sudo bash wolf-cog-os/scripts/fix-boot-restart-loop.sh /dev/sdXN
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-boot-restart-loop.sh /dev/sdXN"
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

echo "Applying boot restart-loop fix on $MNT ..."

for rel in \
  usr/lib/cogos/boot-service-hardening.sh \
  etc/systemd/system/cogos-boot-hardening.service \
  etc/systemd/system/avahi-daemon.service.d/cogos-boot.conf \
  etc/systemd/system/blueman-mechanism.service.d/cogos-boot.conf \
  etc/systemd/system/udisks2.service.d/cogos-boot.conf \
  usr/lib/cogos/firstboot.sh \
  usr/lib/cogos/governance-daemon \
  etc/systemd/system/cogos-spine.service; do
  if [[ -f "$PAYLOAD/$rel" ]]; then
    if [[ "$rel" == *.sh ]] || [[ "$rel" == usr/lib/cogos/* && "$rel" != *.conf ]]; then
      install -D -m755 "$PAYLOAD/$rel" "$MNT/$rel"
    else
      install -D -m644 "$PAYLOAD/$rel" "$MNT/$rel"
    fi
    echo "  installed $rel"
  fi
done

if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1
fi

chroot "$MNT" systemctl enable cogos-boot-hardening.service 2>/dev/null || true
chroot "$MNT" systemctl reset-failed avahi-daemon blueman-mechanism udisks2 2>/dev/null || true

echo ""
echo "Done. Remove USB and boot internal disk."
echo "If still stuck: at GRUB press e, add cogos.safe=1 to the linux line, boot once."
