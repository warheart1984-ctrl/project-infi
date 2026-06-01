#!/usr/bin/env bash
# Repair metal boot stack failures (CRLF launchers, failed cogos-* units).
# Run from Wolf CoG OS live USB:
#   sudo bash wolf-cog-os/scripts/fix-metal-boot-stack.sh /dev/sdXN
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: sudo bash fix-metal-boot-stack.sh /dev/sdXN"
  exit 1
fi

DEV="$1"
MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/../payload"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=lib/normalize-boot-stack-lf.sh
source "$SCRIPT_DIR/lib/normalize-boot-stack-lf.sh"

if ! mountpoint -q "$MNT"; then
  mkdir -p "$MNT"
  mount "$DEV" "$MNT"
fi

echo "Repairing metal boot stack on $MNT ..."

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
  [[ -f "$PAYLOAD/$f" ]] || continue
  if [[ "$f" == *.service || "$f" == *.conf ]]; then
    install -D -m644 "$PAYLOAD/$f" "$MNT/$f"
  else
    install -D -m755 "$PAYLOAD/$f" "$MNT/$f"
  fi
  echo "  installed $f"
done

normalize_boot_stack_lf "$MNT"
verify_boot_stack_lf "$MNT"

# Remove legacy substrate drop-ins that deadlock dbus/accounts before firstboot finishes.
for dropin in \
  etc/systemd/system/accounts-daemon.service.d/cogos-firstboot.conf \
  etc/systemd/system/dbus.service.d/cogos-firstboot.conf \
  etc/systemd/system/systemd-logind.service.d/cogos-firstboot.conf \
  etc/systemd/system/polkit.service.d/cogos-firstboot.conf; do
  rm -f "$MNT/$dropin" 2>/dev/null || true
done
rmdir "$MNT/etc/systemd/system/accounts-daemon.service.d" 2>/dev/null || true
rmdir "$MNT/etc/systemd/system/dbus.service.d" 2>/dev/null || true
rmdir "$MNT/etc/systemd/system/systemd-logind.service.d" 2>/dev/null || true
rmdir "$MNT/etc/systemd/system/polkit.service.d" 2>/dev/null || true
echo "  removed blocking substrate drop-ins"

if [[ -d "$REPO_ROOT/src" && -d "$MNT/opt/cogos/runtime/src" ]]; then
  mkdir -p "$MNT/opt/cogos/runtime/src"
  for module in \
    aais_ul.py \
    aais_ul_substrate.py \
    direct_challenge_module.py \
    jarvis_reasoning_protocol.py \
    jarvis_types.py \
    reasoning_types.py; do
    [[ -f "$REPO_ROOT/src/$module" ]] || continue
    install -D -m644 "$REPO_ROOT/src/$module" "$MNT/opt/cogos/runtime/src/$module"
    echo "  installed opt/cogos/runtime/src/$module"
  done
fi

if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
  chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1 --quiet \
    || echo "WARN: cogos-install-finish returned non-zero"
fi

chroot "$MNT" systemctl disable NetworkManager-wait-online.service systemd-networkd-wait-online.service 2>/dev/null || true
chroot "$MNT" systemctl mask NetworkManager-wait-online.service systemd-networkd-wait-online.service 2>/dev/null || true
chroot "$MNT" systemctl reset-failed cogos-firstboot cogos-governance cogos-spine cogos-observer 2>/dev/null || true
chroot "$MNT" systemctl enable cogos-boot-hardening.service cogos-firstboot.service \
  cogos-governance.service cogos-spine.service cogos-observer.service 2>/dev/null || true

echo ""
echo "Done. Reboot from internal disk."
echo "Check: journalctl -b -u cogos-firstboot -u cogos-governance --no-pager"
