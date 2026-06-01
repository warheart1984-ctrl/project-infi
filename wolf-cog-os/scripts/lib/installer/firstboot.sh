#!/usr/bin/env bash
set -euo pipefail

firstboot_plan() {
  emit_plan_line "Set first-boot handoff"
  emit_plan_line "  marker: /var/lib/cogos/FIRST_BOOT_PENDING"
  emit_plan_line "  hook: enable cogos-firstboot.service when available"
}

firstboot_apply() {
  firstboot_plan

  run_cmd mkdir -p "$TARGET_MOUNT_ROOT/var/lib/cogos"
  run_cmd touch "$TARGET_MOUNT_ROOT/var/lib/cogos/FIRST_BOOT_PENDING"
  run_cmd mkdir -p "$TARGET_MOUNT_ROOT/opt/cogos/memory/logs"

  run_cmd chroot "$TARGET_MOUNT_ROOT" bash -lc "if systemctl list-unit-files | awk '{print \$1}' | grep -q '^cogos-firstboot.service$'; then systemctl enable cogos-firstboot.service cogos-governance.service cogos-spine.service cogos-observer.service; systemctl disable cogos-runtime.service 2>/dev/null || true; elif systemctl list-unit-files | awk '{print \$1}' | grep -q '^cogos-first-boot.service$'; then systemctl enable cogos-first-boot.service; fi"
  run_cmd chroot "$TARGET_MOUNT_ROOT" bash -lc "if command -v cogos-install-finish >/dev/null 2>&1; then cogos-install-finish --post-install || true; fi"

  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    write_install_proof "$TARGET_MOUNT_ROOT"
  fi
}

firstboot_rollback() {
  safe_remove "$TARGET_MOUNT_ROOT/var/lib/cogos/FIRST_BOOT_PENDING"
  safe_remove "$TARGET_MOUNT_ROOT/opt/cogos/memory/logs/install_proof.json"
  run_cmd chroot "$TARGET_MOUNT_ROOT" bash -lc "systemctl disable cogos-firstboot.service cogos-governance.service cogos-spine.service cogos-observer.service cogos-first-boot.service cogos-runtime.service 2>/dev/null || true"
}
