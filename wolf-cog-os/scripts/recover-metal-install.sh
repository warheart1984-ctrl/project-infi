#!/usr/bin/env bash
# Wolf CoG OS — live-USB recovery for bricked internal-disk install.
# Implements: mount → inspect logs/failed units → Wolf fixes → initramfs/grub.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: sudo bash recover-metal-install.sh [options] /dev/sdXN [/dev/sdY1]

  /dev/sdXN   Installed root partition (ext4)
  /dev/sdY1   Optional EFI System Partition (vfat)

Options:
  --inspect-only   Diagnose only (logs + failed units); no repairs
  --skip-grub      Skip update-initramfs / grub-install / update-grub
  --disk DEV       Boot disk for grub-install (e.g. /dev/sda)

Environment:
  MNT=/mnt/cogos-fix   Mount point for root

Examples:
  sudo bash recover-metal-install.sh /dev/nvme0n1p2
  sudo bash recover-metal-install.sh --inspect-only /dev/sda2
  sudo bash recover-metal-install.sh /dev/sda2 /dev/sda1 --disk /dev/sda
EOF
}

INSPECT_ONLY=0
SKIP_GRUB=0
GRUB_DISK=""
ROOT_DEV=""
EFI_DEV=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --inspect-only) INSPECT_ONLY=1; shift ;;
    --skip-grub) SKIP_GRUB=1; shift ;;
    --disk) GRUB_DISK="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    /dev/*)
      if [[ -z "$ROOT_DEV" ]]; then
        ROOT_DEV="$1"
      elif [[ -z "$EFI_DEV" ]]; then
        EFI_DEV="$1"
      else
        echo "ERROR: unexpected argument: $1" >&2
        usage
        exit 1
      fi
      shift
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

[[ -n "$ROOT_DEV" ]] || { usage; exit 1; }

MNT="${MNT:-/mnt/cogos-fix}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$SCRIPT_DIR/../payload"

mount_root() {
  mkdir -p "$MNT"
  if ! mountpoint -q "$MNT"; then
    mount "$ROOT_DEV" "$MNT"
  fi
  if [[ -n "$EFI_DEV" && -b "$EFI_DEV" ]]; then
    mkdir -p "$MNT/boot/efi"
    if ! mountpoint -q "$MNT/boot/efi"; then
      mount "$EFI_DEV" "$MNT/boot/efi"
    fi
  fi
  for spec in /dev /proc /sys /run; do
    mkdir -p "$MNT$spec"
    mount --bind "$spec" "$MNT$spec" 2>/dev/null || true
  done
}

section() {
  echo ""
  echo "=== $* ==="
}

inspect_logs() {
  section "Previous boot logs"
  if [[ -d "$MNT/var/log/journal" ]]; then
    journalctl --directory="$MNT/var/log/journal" -b -1 --no-pager -n 80 2>/dev/null \
      || echo "(journalctl unavailable)"
  else
    echo "No persistent journal under $MNT/var/log/journal"
  fi
  for log in syslog cogos-firstboot.log cogos-governance.log cogos-spine.log \
    cogos-install-finish.log cogos-di-late-command.log; do
    if [[ -f "$MNT/var/log/$log" ]]; then
      echo "--- tail /var/log/$log ---"
      tail -n 40 "$MNT/var/log/$log"
    fi
  done
}

inspect_failed_units() {
  section "Failed systemd units (installed system)"
  chroot "$MNT" systemctl list-units --state=failed --no-pager 2>/dev/null \
    || echo "(systemctl list-units failed)"
  echo ""
  echo "Watch for: accounts-daemon.service display-manager.service systemd-logind.service"
  echo "            dbus.service polkit.service cogos-governance.service"
}

inspect_cogos() {
  section "CoGOS boot state"
  echo -n "PID1: "
  readlink "$MNT/usr/sbin/init" 2>/dev/null || echo "(missing)"
  echo -n "90cogos: "
  if [[ -f "$MNT/etc/init.d/90cogos" ]]; then echo "PRESENT (bad)"; else echo "absent (good)"; fi
  echo -n "governance grace: "
  if [[ -f "$MNT/etc/cog/governance.json" ]]; then
    grep -q 'accounts-daemon.service' "$MNT/etc/cog/governance.json" && echo "configured" || echo "missing entry"
  else
    echo "no /etc/cog/governance.json"
  fi
  for unit in cogos-firstboot cogos-governance cogos-spine cogos-observer accounts-daemon; do
    if [[ -f "$MNT/etc/systemd/system/${unit}.service" ]] \
       || chroot "$MNT" systemctl cat "${unit}.service" >/dev/null 2>&1; then
      echo "  unit: ${unit}.service present"
    fi
  done
}

apply_wolf_repairs() {
  section "Applying Wolf CoG OS repairs"

  rm -f "$MNT/usr/sbin/init" "$MNT/sbin/init"
  ln -sf /lib/systemd/systemd "$MNT/usr/sbin/init"
  [[ -d "$MNT/sbin" ]] && ln -sf /lib/systemd/systemd "$MNT/sbin/init"
  echo "  PID1 -> /lib/systemd/systemd"

  rm -f "$MNT/etc/init.d/90cogos" 2>/dev/null || true
  for rc_dir in "$MNT"/etc/rc*.d; do
    [[ -d "$rc_dir" ]] || continue
    rm -f "$rc_dir"/[SK]??cogos "$rc_dir"/[SK]??90cogos 2>/dev/null || true
  done

  for f in \
    usr/local/bin/cogos-install-finish \
    usr/lib/cogos/firstboot.sh \
    usr/lib/cogos/governance-grace.sh \
    usr/lib/cogos/governance-daemon \
    usr/lib/cogos/spine \
    usr/lib/cogos/observer \
    etc/cog/governance.json \
    etc/systemd/system/cogos-firstboot.service \
    etc/systemd/system/cogos-governance.service \
    etc/systemd/system/cogos-spine.service \
    etc/systemd/system/cogos-observer.service \
    etc/systemd/system/accounts-daemon.service.d/cogos-firstboot.conf; do
    if [[ -f "$PAYLOAD/$f" ]]; then
      if [[ "$f" == *.service || "$f" == *.conf ]]; then
        install -D -m644 "$PAYLOAD/$f" "$MNT/$f"
      else
        install -D -m755 "$PAYLOAD/$f" "$MNT/$f"
      fi
    fi
  done
  find "$MNT/etc/systemd/system" \( -name '*.service' -o -name '*.conf' \) -type f \
    -exec chmod 644 {} + 2>/dev/null || true
  chmod +x "$MNT/usr/lib/cogos/"* 2>/dev/null || true
  if [[ -f "$PAYLOAD/opt/cogos/config/governance_boot.json" ]]; then
    install -D -m644 "$PAYLOAD/opt/cogos/config/governance_boot.json" "$MNT/opt/cogos/config/governance_boot.json"
    install -D -m644 "$PAYLOAD/opt/cogos/config/governance_boot.json" "$MNT/etc/cog/governance.json"
  fi

  chroot "$MNT" bash -c '
    set -eu
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update
      apt-get install -y --reinstall accountsservice dbus policykit-1 systemd-sysv || true
    fi
    systemctl daemon-reload
    systemctl enable accounts-daemon.service dbus.service systemd-logind.service || true
  '

  if [[ -x "$MNT/usr/local/bin/cogos-install-finish" ]]; then
    chroot "$MNT" /usr/local/bin/cogos-install-finish --in-target --keep-systemd-pid1 --quiet \
      || echo "WARN: cogos-install-finish returned non-zero"
  fi
  echo "  Wolf boot stack + accounts-daemon grace applied"
}

rebuild_bootloader() {
  [[ "$SKIP_GRUB" == "1" ]] && return 0
  section "Rebuild initramfs + bootloader"
  chroot "$MNT" bash -c '
    set -eu
    if command -v update-initramfs >/dev/null 2>&1; then
      update-initramfs -u -k all
    fi
  ' || echo "WARN: update-initramfs failed"

  if [[ -n "$GRUB_DISK" && -b "$GRUB_DISK" ]]; then
    chroot "$MNT" grub-install "$GRUB_DISK" || echo "WARN: grub-install failed"
  fi
  if chroot "$MNT" command -v update-grub >/dev/null 2>&1; then
    chroot "$MNT" update-grub || echo "WARN: update-grub failed"
  fi
}

check_kernel_modules() {
  section "Kernel modules on installed system"
  kver="$(chroot "$MNT" uname -r 2>/dev/null || true)"
  if [[ -z "$kver" ]]; then
    kver="$(ls "$MNT/lib/modules" 2>/dev/null | head -1 || true)"
  fi
  if [[ -n "$kver" && -d "$MNT/lib/modules/$kver" ]]; then
    echo "  /lib/modules/$kver present ($(find "$MNT/lib/modules/$kver" -name '*.ko*' 2>/dev/null | wc -l) modules)"
  else
    echo "  WARN: no kernel modules tree found under /lib/modules"
  fi
}

# --- main ---
mount_root
inspect_logs
inspect_failed_units
inspect_cogos
check_kernel_modules

if [[ "$INSPECT_ONLY" == "1" ]]; then
  echo ""
  echo "Inspect-only complete. Re-run without --inspect-only to repair."
  exit 0
fi

apply_wolf_repairs
rebuild_bootloader

echo ""
echo "Recovery complete. Remove USB and reboot from internal disk."
echo "After boot:"
echo "  systemctl status accounts-daemon.service cogos-governance.service cogos-spine.service"
echo "  journalctl -b -p err"
