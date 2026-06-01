#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/live-systemd-init.sh
source "$SCRIPT_DIR/lib/live-systemd-init.sh"

ROOTFS=""
ISO_TREE=""
PROOF_DIR=""
PLYMOUTH_POLICY="optional"

usage() {
  cat <<'USAGE'
Usage:
  bash wolf-cog-os/scripts/validate-live-boot-integrity.sh \
    --rootfs <path> \
    --iso-tree <path> \
    --proof-dir <path> \
    [--plymouth-policy required|optional|forbidden]
USAGE
}

log() {
  printf '[validate-boot] %s\n' "$1"
}

die() {
  printf '[validate-boot][ERROR] %s\n' "$1" >&2
  exit "${2:-1}"
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
      --rootfs)
        ROOTFS="${2:-}"
        shift 2
        ;;
      --rootfs=*)
        ROOTFS="${1#*=}"
        shift
        ;;
      --iso-tree)
        ISO_TREE="${2:-}"
        shift 2
        ;;
      --iso-tree=*)
        ISO_TREE="${1#*=}"
        shift
        ;;
      --proof-dir)
        PROOF_DIR="${2:-}"
        shift 2
        ;;
      --proof-dir=*)
        PROOF_DIR="${1#*=}"
        shift
        ;;
      --plymouth-policy)
        PLYMOUTH_POLICY="${2:-}"
        shift 2
        ;;
      --plymouth-policy=*)
        PLYMOUTH_POLICY="${1#*=}"
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die "unknown argument: $1" 2
        ;;
    esac
  done
}

verify_init_target() {
  local systemd_target
  local init_path="$ROOTFS/usr/sbin/init"
  local sbin_init="$ROOTFS/sbin/init"

  systemd_target="$(resolve_live_systemd_init "$ROOTFS")" || \
    die "missing live systemd target under /lib or /usr/lib" 10
  [[ -e "$init_path" ]] || die "missing init target: $init_path" 10

  same_init_in_rootfs "$ROOTFS" "$init_path" "$systemd_target" || \
    die "live /usr/sbin/init must resolve to systemd inside rootfs (got: $(readlink "$init_path" 2>/dev/null || echo missing))" 10

  if [[ -e "$ROOTFS/sbin" ]]; then
    [[ -e "$sbin_init" ]] || die "missing init target: $sbin_init" 10
    same_init_in_rootfs "$ROOTFS" "$sbin_init" "$systemd_target" || \
      die "live /sbin/init must resolve to systemd inside rootfs (got: $(readlink "$sbin_init" 2>/dev/null || echo missing))" 10
    printf 'sbin_init_target=%s\n' "$(resolve_init_link_target_in_rootfs "$ROOTFS" "$sbin_init")" >>"$PROOF_DIR/summary.txt"
  fi

  printf 'systemd_target=%s\n' "$systemd_target" >>"$PROOF_DIR/summary.txt"
  printf 'usr_sbin_init_target=%s\n' "$(resolve_init_link_target_in_rootfs "$ROOTFS" "$init_path")" >>"$PROOF_DIR/summary.txt"
}

collect_plymouth_references() {
  local refs_file="$PROOF_DIR/plymouth-references.txt"
  : >"$refs_file"

  local candidates=(
    "$ROOTFS/etc/init.d"
    "$ROOTFS/etc/initramfs-tools"
    "$ROOTFS/usr/lib/systemd/system"
  )
  local c
  for c in "${candidates[@]}"; do
    if [[ -d "$c" ]]; then
      grep -R --line-number --fixed-strings "/usr/bin/plymouth" "$c" >>"$refs_file" || true
    fi
  done

  local plymouth_bin="$ROOTFS/usr/bin/plymouth"
  local has_ref=0
  local has_bin=0
  [[ -s "$refs_file" ]] && has_ref=1
  [[ -x "$plymouth_bin" || -f "$plymouth_bin" ]] && has_bin=1

  case "$PLYMOUTH_POLICY" in
    required)
      [[ "$has_ref" -eq 1 ]] || die "plymouth policy required, but no /usr/bin/plymouth references found" 11
      [[ "$has_bin" -eq 1 ]] || die "plymouth policy required, but binary missing at /usr/bin/plymouth" 11
      ;;
    optional)
      if [[ "$has_ref" -eq 1 && "$has_bin" -ne 1 ]]; then
        die "plymouth referenced but binary missing (policy=optional, live-safe violation)" 11
      fi
      ;;
    forbidden)
      [[ "$has_ref" -eq 0 ]] || die "plymouth policy forbidden, but /usr/bin/plymouth is referenced" 11
      ;;
    *)
      die "invalid plymouth policy: $PLYMOUTH_POLICY" 2
      ;;
  esac

  printf 'plymouth_policy=%s\n' "$PLYMOUTH_POLICY" >>"$PROOF_DIR/summary.txt"
  printf 'plymouth_references=%s\n' "$has_ref" >>"$PROOF_DIR/summary.txt"
  printf 'plymouth_binary_present=%s\n' "$has_bin" >>"$PROOF_DIR/summary.txt"
}

verify_fedora_family_iso_boot() {
  local pxeboot="$ISO_TREE/images/pxeboot"
  [[ -f "$ISO_TREE/images/install.img" ]] || return 1
  [[ -f "$pxeboot/vmlinuz" && -f "$pxeboot/initrd.img" ]] || \
    die "fedora-family ISO missing pxeboot kernel/initrd under images/pxeboot" 12

  local grub_cfg=""
  for grub_cfg in \
    "$ISO_TREE/boot/grub2/grub.cfg" \
    "$ISO_TREE/EFI/BOOT/grub.cfg" \
    "$ISO_TREE/boot/grub/grub.cfg"; do
    if [[ -f "$grub_cfg" ]]; then
      printf 'grub_boot_mode=fedora-installer\n' >>"$PROOF_DIR/summary.txt"
      printf 'grub_config=%s\n' "$grub_cfg" >>"$PROOF_DIR/summary.txt"
      printf 'squashfs_artifact=/images/install.img\n' >>"$PROOF_DIR/summary.txt"
      return 0
    fi
  done
  die "fedora-family ISO missing grub.cfg (boot/grub2 or EFI/BOOT)" 12
}

verify_grub_squashfs_consistency() {
  local grub_dir="$ISO_TREE/boot/grub"
  local live_dir="$ISO_TREE/live"
  local lines="$PROOF_DIR/grub-squashfs-lines.txt"
  : >"$lines"

  if verify_fedora_family_iso_boot; then
    return 0
  fi

  [[ -d "$grub_dir" ]] || die "missing GRUB directory: $grub_dir" 12
  [[ -f "$live_dir/filesystem.squashfs" ]] || die "missing live squashfs artifact: $live_dir/filesystem.squashfs" 12

  grep -R --line-number --fixed-strings "filesystem.squashfs" "$grub_dir" >>"$lines" 2>/dev/null || true
  if [[ -s "$lines" ]]; then
    if grep -R --line-number --fixed-strings "filesystem.squashfs" "$grub_dir" | grep -v "/live/filesystem.squashfs" >/dev/null 2>&1; then
      die "inconsistent squashfs path detected in GRUB entries (expected /live/filesystem.squashfs)" 12
    fi
    printf 'grub_boot_mode=grub-squashfs-reference\n' >>"$PROOF_DIR/summary.txt"
    printf 'grub_squashfs_path=/live/filesystem.squashfs\n' >>"$PROOF_DIR/summary.txt"
    return 0
  fi

  if [[ -f "$grub_dir/grub.cfg" ]] && grep -q '/live/vmlinuz' "$grub_dir/grub.cfg" && grep -q '/live/initrd' "$grub_dir/grub.cfg"; then
    grep -n '/live/vmlinuz\|/live/initrd' "$grub_dir/grub.cfg" >>"$lines" || true
    printf 'grub_boot_mode=live-kernel-initrd\n' >>"$PROOF_DIR/summary.txt"
    printf 'grub_squashfs_path=/live/filesystem.squashfs\n' >>"$PROOF_DIR/summary.txt"
    return 0
  fi

  die "GRUB live boot contract not satisfied (need squashfs refs or /live/vmlinuz+/live/initrd entries)" 12
}

verify_grub_init_contract() {
  if [[ -f "$ISO_TREE/images/install.img" ]]; then
    printf 'grub_init_contract=fedora-installer-skip\n' >>"$PROOF_DIR/summary.txt"
    return 0
  fi

  local grub_dir="$ISO_TREE/boot/grub"
  local init_lines="$PROOF_DIR/grub-init-lines.txt"
  : >"$init_lines"
  grep -R --line-number --fixed-strings " init=" "$grub_dir" >>"$init_lines" || true

  if [[ -s "$init_lines" ]]; then
    if grep -Ev 'init=/lib/systemd/systemd|init=/usr/lib/systemd/systemd' "$init_lines" >/dev/null 2>&1; then
      die "GRUB init= contract violation (only systemd init allowed for live-safe builds)" 13
    fi
  fi
  printf 'grub_init_contract=systemd-only\n' >>"$PROOF_DIR/summary.txt"
}

emit_validation_json() {
  python3 - "$PROOF_DIR/validation.json" <<PY
import json
import sys
from datetime import datetime, timezone

data = {
    "claim_taxonomy": "proven",
    "why": "Boot-critical integrity checks passed for init target, plymouth policy handling, and GRUB squashfs consistency.",
    "rootfs": "${ROOTFS}",
    "iso_tree": "${ISO_TREE}",
    "plymouth_policy": "${PLYMOUTH_POLICY}",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "evidence_files": [
        "summary.txt",
        "plymouth-references.txt",
        "grub-squashfs-lines.txt",
        "grub-init-lines.txt",
    ],
}
with open(sys.argv[1], "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
}

main() {
  parse_args "$@"
  [[ -d "$ROOTFS" ]] || die "rootfs dir missing: $ROOTFS" 3
  [[ -d "$ISO_TREE" ]] || die "iso tree dir missing: $ISO_TREE" 3
  [[ -n "$PROOF_DIR" ]] || die "proof dir is required" 2
  mkdir -p "$PROOF_DIR"
  : >"$PROOF_DIR/summary.txt"

  verify_init_target
  collect_plymouth_references
  verify_grub_squashfs_consistency
  verify_grub_init_contract
  emit_validation_json

  log "validation complete: $PROOF_DIR"
}

main "$@"
