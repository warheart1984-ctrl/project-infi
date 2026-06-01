#!/usr/bin/env bash
# Canonical CoGOS boot stack: 4 native systemd units (no substrate drop-in deadlocks).
set -euo pipefail

COGOS_BOOT_STACK_UNITS=(
  etc/systemd/system/cogos-firstboot.service
  etc/systemd/system/cogos-governance.service
  etc/systemd/system/cogos-spine.service
  etc/systemd/system/cogos-observer.service
)

COGOS_BOOT_HARDENING_ARTIFACTS=(
  etc/systemd/system/cogos-boot-hardening.service
  etc/systemd/system/avahi-daemon.service.d/cogos-boot.conf
  etc/systemd/system/blueman-mechanism.service.d/cogos-boot.conf
  etc/systemd/system/udisks2.service.d/cogos-boot.conf
)

COGOS_BOOT_LAUNCHERS=(
  firstboot.sh
  governance-grace.sh
  governance-daemon
  spine
  observer
  boot-service-hardening.sh
)

cogos_boot_stack_count() {
  printf '%s' "${#COGOS_BOOT_STACK_UNITS[@]}"
}

install_cogos_boot_stack_file() {
  local payload_root="$1"
  local target_root="$2"
  local rel="$3"
  local src="$payload_root/$rel"
  local dst="$target_root/$rel"
  [[ -f "$src" ]] || return 1
  mkdir -p "$(dirname "$dst")"
  install -D -m644 "$src" "$dst"
}

normalize_cogos_systemd_unit_modes() {
  local root="${1:-}"
  local dir
  for dir in "$root/etc/systemd/system" "$root/etc/systemd/system"/*.service.d; do
    [[ -d "$dir" ]] || continue
    find "$dir" -maxdepth 1 \( -name '*.service' -o -name '*.conf' \) -type f \
      -exec chmod 644 {} + 2>/dev/null || true
  done
}

verify_cogos_boot_stack_present() {
  local root="${1:?}"
  local rel missing=0
  for rel in "${COGOS_BOOT_STACK_UNITS[@]}"; do
    [[ -f "$root/$rel" ]] || {
      echo "missing boot stack artifact: $root/$rel" >&2
      missing=1
    }
  done
  return "$missing"
}
