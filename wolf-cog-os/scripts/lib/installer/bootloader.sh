#!/usr/bin/env bash
set -euo pipefail

bootloader_plan() {
  emit_plan_line "Install bootloader"
  emit_plan_line "  grub-install target disk: $TARGET_DISK"
}

is_mounted_path_bootloader() {
  local mount_path="$1"
  awk -v m="$mount_path" '$5 == m { found=1; exit } END { exit(found ? 0 : 1) }' /proc/self/mountinfo 2>/dev/null
}

ensure_bootloader_bind_mount() {
  local source_path="$1"
  local target_path="$2"
  local state_key="$3"
  run_cmd mkdir -p "$target_path"
  if ! is_mounted_path_bootloader "$target_path"; then
    run_cmd mount --bind "$source_path" "$target_path"
  fi
  set_state_value "$state_key" "$target_path"
}

bootloader_apply() {
  bootloader_plan

  # Resume may skip copy as "completed" even though mounts were cleaned up.
  ensure_target_mounts
  ensure_bootloader_bind_mount /dev "$TARGET_MOUNT_ROOT/dev" bind_dev
  ensure_bootloader_bind_mount /proc "$TARGET_MOUNT_ROOT/proc" bind_proc
  ensure_bootloader_bind_mount /sys "$TARGET_MOUNT_ROOT/sys" bind_sys

  run_cmd chroot "$TARGET_MOUNT_ROOT" grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=CoGOS
  run_cmd chroot "$TARGET_MOUNT_ROOT" grub-install --target=i386-pc "$TARGET_DISK"
  run_cmd chroot "$TARGET_MOUNT_ROOT" update-grub
}

bootloader_rollback() {
  local bind_sys bind_proc bind_dev
  bind_sys="$(get_state_value bind_sys)"
  bind_proc="$(get_state_value bind_proc)"
  bind_dev="$(get_state_value bind_dev)"
  if [[ -n "$bind_sys" ]] && is_mounted_path_bootloader "$bind_sys"; then
    run_cmd umount -lf "$bind_sys" || true
  fi
  if [[ -n "$bind_proc" ]] && is_mounted_path_bootloader "$bind_proc"; then
    run_cmd umount -lf "$bind_proc" || true
  fi
  if [[ -n "$bind_dev" ]] && is_mounted_path_bootloader "$bind_dev"; then
    run_cmd umount -lf "$bind_dev" || true
  fi
}
