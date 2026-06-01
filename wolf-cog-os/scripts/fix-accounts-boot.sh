#!/usr/bin/env bash
# Levels 1–3: repair accounts-daemon + CoGOS bootstrap grace on installed disk.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-accounts-boot.sh /dev/sdXN"
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

echo "Repairing accounts-daemon + CoGOS bootstrap grace on $MNT ..."

for f in \
  usr/lib/cogos/firstboot.sh \
  usr/lib/cogos/governance-grace.sh \
  usr/lib/cogos/governance-daemon \
  etc/cog/governance.json \
  etc/systemd/system/cogos-firstboot.service \
  etc/systemd/system/cogos-governance.service \
  etc/systemd/system/accounts-daemon.service.d/cogos-firstboot.conf; do
  if [[ -f "$PAYLOAD/$f" ]]; then
    if [[ "$f" == *.service || "$f" == *.conf ]]; then
      install -D -m644 "$PAYLOAD/$f" "$MNT/$f"
    else
      install -D -m755 "$PAYLOAD/$f" "$MNT/$f"
    fi
    echo "  installed $f"
  fi
done

find "$MNT/etc/systemd/system" \( -name '*.service' -o -name '*.conf' \) -type f \
  -exec chmod 644 {} + 2>/dev/null || true

if [[ -f "$PAYLOAD/opt/cogos/config/governance_boot.json" ]]; then
  install -D -m644 "$PAYLOAD/opt/cogos/config/governance_boot.json" "$MNT/opt/cogos/config/governance_boot.json"
  install -D -m644 "$PAYLOAD/opt/cogos/config/governance_boot.json" "$MNT/etc/cog/governance.json"
  install -D -m644 "$PAYLOAD/opt/cogos/config/governance_boot.json" "$MNT/etc/cogos/governance.json"
fi

chroot "$MNT" bash -c '
  set -eu
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y --reinstall accountsservice dbus policykit-1
  fi
  systemctl daemon-reload
  systemctl enable accounts-daemon.service dbus.service systemd-logind.service || true
'

if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1 --quiet
fi

echo "Done. Reboot from internal disk."
echo "Check: systemctl status accounts-daemon.service cogos-governance.service"
