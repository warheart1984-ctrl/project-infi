#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/installer/common.sh
source "$SCRIPT_DIR/lib/installer/common.sh"
# shellcheck source=lib/installer/disk.sh
source "$SCRIPT_DIR/lib/installer/disk.sh"
# shellcheck source=lib/installer/copy.sh
source "$SCRIPT_DIR/lib/installer/copy.sh"
# shellcheck source=lib/installer/bootloader.sh
source "$SCRIPT_DIR/lib/installer/bootloader.sh"
# shellcheck source=lib/installer/identity.sh
source "$SCRIPT_DIR/lib/installer/identity.sh"
# shellcheck source=lib/installer/network.sh
source "$SCRIPT_DIR/lib/installer/network.sh"
# shellcheck source=lib/installer/firstboot.sh
source "$SCRIPT_DIR/lib/installer/firstboot.sh"

usage() {
  cat <<'USAGE'
Usage:
  bash wolf-cog-os/scripts/cogos-installer.sh [options]

Modes:
  Default is plan-only (no disk writes). Use --apply for actual install.

Options:
  --target-disk /dev/sdX|/dev/nvme0n1   Install target disk
  --rootfs /path/to/rootfs              Rootfs source (default: COGOS_ROOTFS_SRC)
  --hostname NAME                       Installed hostname (default: wolf-cog-os)
  --user NAME                           Installed user (default: operator)
  --password PASS                       Optional password for installed user
  --state-dir PATH                      Checkpoint/log state directory
  --resume                              Resume from previous checkpoints
  --no-rollback                         Disable rollback on failure
  --apply                               Execute install actions
  --yes                                 Skip confirmation prompt
  --non-interactive                     Disable TUI prompts
  --smoke                               Validate module wiring and tooling
  COGOS_INSTALLER_FAIL_STEP             Inject a one-time failure at step name
  -h, --help                            Show help
USAGE
}

INSTALLER_APPLY=0
ASSUME_YES=0
NON_INTERACTIVE=0
INSTALL_SMOKE=0
INSTALLER_RESUME=0
ROLLBACK_ON_FAILURE=1
STATE_DIR_SET=0
TARGET_DISK="${TARGET_DISK:-}"
ROOTFS_SOURCE="${COGOS_ROOTFS_SRC:-$WOLF_ROOTFS_OUT}"
INSTALL_HOSTNAME="${COGOS_INSTALL_HOSTNAME:-wolf-cog-os}"
INSTALL_USER="${COGOS_INSTALL_USER:-operator}"
INSTALL_PASSWORD="${COGOS_INSTALL_PASSWORD:-}"
INSTALLER_VERSION="${COGOS_INSTALLER_VERSION:-0.2.0}"
INJECT_FAIL_STEP="${COGOS_INSTALLER_FAIL_STEP:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-disk) TARGET_DISK="${2:-}"; shift 2 ;;
    --rootfs) ROOTFS_SOURCE="${2:-}"; shift 2 ;;
    --hostname) INSTALL_HOSTNAME="${2:-}"; shift 2 ;;
    --user) INSTALL_USER="${2:-}"; shift 2 ;;
    --password) INSTALL_PASSWORD="${2:-}"; shift 2 ;;
    --state-dir) INSTALLER_STATE_DIR="${2:-}"; STATE_DIR_SET=1; shift 2 ;;
    --resume) INSTALLER_RESUME=1; shift ;;
    --no-rollback) ROLLBACK_ON_FAILURE=0; shift ;;
    --apply) INSTALLER_APPLY=1; shift ;;
    --yes) ASSUME_YES=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --smoke) INSTALL_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
done

if [[ "$INSTALL_SMOKE" == "1" ]]; then
  init_installer_state 0
  start_install_log_capture "smoke"
  set_state_value run_mode "smoke"
  set_state_value installer_version "$INSTALLER_VERSION"
  set_state_value cogos_tag "${COGOS_TAG:-unknown}"
  set_state_value target_disk "${TARGET_DISK:-unknown}"
  set_state_value rootfs_source "$ROOTFS_SOURCE"
  set_state_value install_hostname "$INSTALL_HOSTNAME"
  set_state_value install_user "$INSTALL_USER"
  set_state_value step_order "disk,copy,bootloader,identity,network,firstboot"
  refresh_state_json
  log "Installer smoke OK: module load + tool checks passed."
  exit 0
fi

if [[ "$STATE_DIR_SET" != "1" ]]; then
  if [[ "$INSTALLER_APPLY" == "1" ]]; then
    INSTALLER_STATE_DIR="/var/log/cogos-installer"
  else
    INSTALLER_STATE_DIR="/tmp/cogos-installer"
  fi
fi
init_installer_state "$INSTALLER_RESUME"
start_install_log_capture "$( [[ "$INSTALLER_APPLY" == "1" ]] && echo apply || echo plan )"

require_tools lsblk awk sed grep rsync parted mkfs.vfat mkfs.ext4 mount umount chroot grub-install sfdisk partprobe

ROOTFS_SOURCE="$(readlink -f "$ROOTFS_SOURCE" 2>/dev/null || echo "$ROOTFS_SOURCE")"
[[ -d "$ROOTFS_SOURCE" ]] || die "Rootfs source not found: $ROOTFS_SOURCE"
[[ -f "$ROOTFS_SOURCE/etc/os-release" ]] || die "Invalid rootfs source: missing etc/os-release"

if [[ -z "$TARGET_DISK" && "$NON_INTERACTIVE" == "1" ]]; then
  die "--target-disk is required in --non-interactive mode."
fi

if [[ -z "$TARGET_DISK" ]]; then
  if command -v whiptail >/dev/null 2>&1; then
    mapfile -t disks < <(lsblk -dpno NAME,SIZE,MODEL | awk '{print $1 " (" $2 " " $3 " " $4 ")"}')
    if [[ "${#disks[@]}" -eq 0 ]]; then
      die "No disks available for install."
    fi
    menu_args=()
    for entry in "${disks[@]}"; do
      disk_name="$(awk '{print $1}' <<<"$entry")"
      menu_args+=("$disk_name" "$entry")
    done
    TARGET_DISK="$(whiptail --title 'CoGOS Installer' --menu 'Select target disk' 20 80 10 "${menu_args[@]}" 3>&1 1>&2 2>&3)" || die "Disk selection cancelled."
  else
    log "Available disks:"
    lsblk -dpno NAME,SIZE,MODEL
    read -r -p "Enter target disk (for example /dev/sda): " TARGET_DISK
  fi
fi

[[ -b "$TARGET_DISK" ]] || die "Target disk is not a block device: $TARGET_DISK"

if [[ "$INSTALLER_APPLY" == "1" ]]; then
  require_root
fi

set_state_value target_disk "$TARGET_DISK"
set_state_value rootfs_source "$ROOTFS_SOURCE"
set_state_value install_hostname "$INSTALL_HOSTNAME"
set_state_value install_user "$INSTALL_USER"
set_state_value installer_version "$INSTALLER_VERSION"
set_state_value run_mode "$( [[ "$INSTALLER_APPLY" == "1" ]] && echo apply || echo plan )"
set_state_value cogos_tag "${COGOS_TAG:-unknown}"
set_state_value step_order "disk,copy,bootloader,identity,network,firstboot"

if [[ "$INSTALLER_RESUME" != "1" ]]; then
  reset_plan
fi
disk_plan "$TARGET_DISK"
copy_plan
bootloader_plan
identity_plan
network_plan
firstboot_plan
refresh_state_json

log "Planned installation:"
cat "$INSTALLER_PLAN_FILE"
log "State directory: $INSTALLER_STATE_DIR"
log "Log file: $INSTALLER_LOG_FILE"
log "State export: $INSTALLER_STATE_JSON"

if [[ "$INSTALLER_APPLY" != "1" ]]; then
  log "Plan mode complete. Re-run with --apply to execute."
  exit 0
fi

if [[ "$ASSUME_YES" != "1" ]]; then
  if command -v whiptail >/dev/null 2>&1; then
    whiptail --title 'CoGOS Installer' --yesno "Install to $TARGET_DISK?\nThis will erase the disk." 12 70 || die "Install cancelled."
  else
    read -r -p "Install to $TARGET_DISK and erase data? (yes/no): " confirm
    [[ "$confirm" == "yes" ]] || die "Install cancelled."
  fi
fi

cleanup_mounts() {
  bootloader_rollback || true
  copy_rollback || true
}
trap cleanup_mounts EXIT

run_step() {
  local step="$1"
  shift
  if is_step_completed "$step"; then
    log "Skipping completed step: $step"
    append_event "resume-skip" "$step" "already completed"
    return 0
  fi
  step_start "$step"
  if "$@"; then
    step_complete "$step"
    return 0
  fi
  return 1
}

rollback_completed_steps() {
  local step status
  log "Rollback started (best effort)."
  for step in firstboot network identity bootloader copy disk; do
    status="$(checkpoint_status "$step")"
    if [[ "$status" != "pending" ]]; then
      append_event "rollback" "$step" "begin"
      case "$step" in
        firstboot) firstboot_rollback || true ;;
        network) network_rollback || true ;;
        identity) identity_rollback || true ;;
        bootloader) bootloader_rollback || true ;;
        copy) copy_rollback || true ;;
        disk) disk_rollback "$TARGET_DISK" || true ;;
      esac
      append_event "rollback" "$step" "done"
    fi
  done
  log "Rollback finished."
}

execute_or_fail() {
  local step="$1"
  shift
  if [[ -n "$INJECT_FAIL_STEP" && "$step" == "$INJECT_FAIL_STEP" ]]; then
    if [[ "$(get_state_value fail_injected_${step})" != "1" ]]; then
      set_state_value "fail_injected_${step}" "1"
      step_start "$step"
      step_fail "$step" "injected failure at step ${step}"
      clear_current_step
      append_event "failure-injected" "$step" "simulated failure for resume/rollback testing"
      if [[ "$ROLLBACK_ON_FAILURE" == "1" ]]; then
        rollback_completed_steps
      fi
      die "Injected failure at step: $step"
    fi
  fi
  if ! run_step "$step" "$@"; then
    step_fail "$step" "execution failed"
    clear_current_step
    append_event "failure" "$step" "step execution failed"
    if [[ "$ROLLBACK_ON_FAILURE" == "1" ]]; then
      rollback_completed_steps
    else
      warn "Rollback disabled (--no-rollback)."
    fi
    die "Installer failed at step: $step. Resume with --resume after fixing the issue."
  fi
}

log "Applying installer steps..."
execute_or_fail disk disk_apply "$TARGET_DISK"
execute_or_fail copy copy_apply
execute_or_fail bootloader bootloader_apply
execute_or_fail identity identity_apply
execute_or_fail network network_apply
execute_or_fail firstboot firstboot_apply

clear_current_step
append_event "complete" "installer" "all steps completed"
log "Install complete for $TARGET_DISK"
