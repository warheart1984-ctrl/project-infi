#!/usr/bin/env bash
set -euo pipefail

disk_plan() {
  local disk="$1"
  local suffix
  suffix="$(part_suffix "$disk")"

  EFI_PART="${disk}${suffix}1"
  ROOT_PART="${disk}${suffix}2"
  DATA_PART="${disk}${suffix}3"

  emit_plan_line "Disk layout for $disk"
  emit_plan_line "  EFI : $EFI_PART (fat32, 512MiB)"
  emit_plan_line "  ROOT: $ROOT_PART (ext4, COGOS_ROOT)"
  emit_plan_line "  DATA: $DATA_PART (ext4, COGOSDATA)"
}

disk_apply() {
  local disk="$1"
  disk_plan "$disk"

  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    sfdisk --dump "$disk" >"$INSTALLER_STATE_DIR/partition-table.backup"
    set_state_value disk_backup "$INSTALLER_STATE_DIR/partition-table.backup"
  else
    emit_plan_line "  backup: $INSTALLER_STATE_DIR/partition-table.backup"
  fi

  run_cmd parted -s "$disk" mklabel gpt
  run_cmd parted -s "$disk" mkpart EFI fat32 1MiB 513MiB
  run_cmd parted -s "$disk" set 1 esp on
  run_cmd parted -s "$disk" mkpart COGOS_ROOT ext4 513MiB 80%
  run_cmd parted -s "$disk" mkpart COGOSDATA ext4 80% 100%

  run_cmd mkfs.vfat -F 32 -n EFI "$EFI_PART"
  run_cmd mkfs.ext4 -F -L COGOS_ROOT "$ROOT_PART"
  run_cmd mkfs.ext4 -F -L COGOSDATA "$DATA_PART"
}

disk_rollback() {
  local disk="$1"
  local backup
  backup="$(get_state_value disk_backup)"
  if [[ -n "$backup" && -f "$backup" ]]; then
    warn "Rolling back disk partition table from backup: $backup"
    run_cmd sfdisk "$disk" <"$backup"
    run_cmd partprobe "$disk" || true
  else
    warn "No disk backup available; cannot restore previous partition table."
  fi
}
