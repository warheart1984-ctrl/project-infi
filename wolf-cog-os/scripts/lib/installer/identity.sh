#!/usr/bin/env bash
set -euo pipefail

identity_plan() {
  emit_plan_line "Configure identity"
  emit_plan_line "  hostname: $INSTALL_HOSTNAME"
  emit_plan_line "  user: $INSTALL_USER"
}

identity_apply() {
  identity_plan

  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    [[ -f "$TARGET_MOUNT_ROOT/etc/hostname" ]] && cp -a "$TARGET_MOUNT_ROOT/etc/hostname" "$TARGET_MOUNT_ROOT/etc/hostname.cogos-installer.bak" || true
    [[ -f "$TARGET_MOUNT_ROOT/etc/hosts" ]] && cp -a "$TARGET_MOUNT_ROOT/etc/hosts" "$TARGET_MOUNT_ROOT/etc/hosts.cogos-installer.bak" || true
  fi
  run_cmd bash -lc "echo '$INSTALL_HOSTNAME' > '$TARGET_MOUNT_ROOT/etc/hostname'"
  run_cmd bash -lc "printf '127.0.0.1\tlocalhost\n127.0.1.1\t%s\n' '$INSTALL_HOSTNAME' > '$TARGET_MOUNT_ROOT/etc/hosts'"

  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    if ! chroot "$TARGET_MOUNT_ROOT" id "$INSTALL_USER" >/dev/null 2>&1; then
      set_state_value identity_user_created "1"
      run_cmd chroot "$TARGET_MOUNT_ROOT" useradd -m -s /bin/bash "$INSTALL_USER" || true
    fi
  else
    run_cmd chroot "$TARGET_MOUNT_ROOT" useradd -m -s /bin/bash "$INSTALL_USER" || true
  fi
  run_cmd chroot "$TARGET_MOUNT_ROOT" usermod -aG sudo "$INSTALL_USER" || true
  if [[ -n "${INSTALL_PASSWORD:-}" ]]; then
    run_cmd bash -lc "echo '$INSTALL_USER:$INSTALL_PASSWORD' | chroot '$TARGET_MOUNT_ROOT' chpasswd"
  else
    run_cmd chroot "$TARGET_MOUNT_ROOT" passwd -d "$INSTALL_USER" || true
  fi
}

identity_rollback() {
  if [[ -f "$TARGET_MOUNT_ROOT/etc/hostname.cogos-installer.bak" ]]; then
    run_cmd mv -f "$TARGET_MOUNT_ROOT/etc/hostname.cogos-installer.bak" "$TARGET_MOUNT_ROOT/etc/hostname"
  fi
  if [[ -f "$TARGET_MOUNT_ROOT/etc/hosts.cogos-installer.bak" ]]; then
    run_cmd mv -f "$TARGET_MOUNT_ROOT/etc/hosts.cogos-installer.bak" "$TARGET_MOUNT_ROOT/etc/hosts"
  fi
  if [[ "$(get_state_value identity_user_created)" == "1" ]]; then
    run_cmd chroot "$TARGET_MOUNT_ROOT" userdel -r "$INSTALL_USER" || true
  fi
}
