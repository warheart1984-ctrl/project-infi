#!/usr/bin/env bash
set -euo pipefail

TARGET_MOUNT_ROOT="${TARGET_MOUNT_ROOT:-/mnt/cogos-target}"

is_mounted_path() {
  local mount_path="$1"
  awk -v m="$mount_path" '$5 == m { found=1; exit } END { exit(found ? 0 : 1) }' /proc/self/mountinfo 2>/dev/null
}

copy_plan() {
  emit_plan_line "Copy rootfs"
  emit_plan_line "  source: $ROOTFS_SOURCE"
  emit_plan_line "  target: $TARGET_MOUNT_ROOT"
}

ensure_target_mounts() {
  run_cmd mkdir -p "$TARGET_MOUNT_ROOT"
  if ! is_mounted_path "$TARGET_MOUNT_ROOT"; then
    run_cmd mount "$ROOT_PART" "$TARGET_MOUNT_ROOT"
  fi
  set_state_value mount_root "$TARGET_MOUNT_ROOT"

  run_cmd mkdir -p "$TARGET_MOUNT_ROOT/boot/efi"
  if ! is_mounted_path "$TARGET_MOUNT_ROOT/boot/efi"; then
    run_cmd mount "$EFI_PART" "$TARGET_MOUNT_ROOT/boot/efi"
  fi
  set_state_value mount_efi "$TARGET_MOUNT_ROOT/boot/efi"

  run_cmd mkdir -p "$TARGET_MOUNT_ROOT/opt/cogos/data"
  if ! is_mounted_path "$TARGET_MOUNT_ROOT/opt/cogos/data"; then
    run_cmd mount "$DATA_PART" "$TARGET_MOUNT_ROOT/opt/cogos/data"
  fi
  set_state_value mount_data "$TARGET_MOUNT_ROOT/opt/cogos/data"
}

copy_apply() {
  copy_plan

  ensure_target_mounts

  run_cmd rsync -aHAX --delete \
    --exclude '/boot/efi/***' \
    --exclude '/dev/*' \
    --exclude '/opt/cogos/data/***' \
    --exclude '/proc/*' \
    --exclude '/sys/*' \
    --exclude '/tmp/*' \
    --exclude '/run/*' \
    "$ROOTFS_SOURCE/" "$TARGET_MOUNT_ROOT/"
}

copy_rollback() {
  local data_mount efi_mount root_mount
  data_mount="$(get_state_value mount_data)"
  efi_mount="$(get_state_value mount_efi)"
  root_mount="$(get_state_value mount_root)"

  if [[ -n "$data_mount" ]] && is_mounted_path "$data_mount"; then
    run_cmd umount -lf "$data_mount" || true
  fi
  if [[ -n "$efi_mount" ]] && is_mounted_path "$efi_mount"; then
    run_cmd umount -lf "$efi_mount" || true
  fi
  if [[ -n "$root_mount" ]] && is_mounted_path "$root_mount"; then
    run_cmd umount -lf "$root_mount" || true
  fi
}
