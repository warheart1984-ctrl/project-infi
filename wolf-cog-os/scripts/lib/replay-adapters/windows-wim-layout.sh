#!/usr/bin/env bash
# Windows WIM/WinPE replay adapter (P15 universal substrate).
set -euo pipefail

adapter_resolve_sfs() {
  local work_iso="$1"
  INSTALL_WIM=""
  BOOT_WIM=""
  BCD_STORE=""
  local candidate
  for candidate in \
    "$work_iso/sources/install.wim" \
    "$work_iso/sources/install.esd" \
    "$work_iso/sources/boot.wim" \
    "$(find "$work_iso/sources" -maxdepth 1 -type f \( -name 'install.wim' -o -name 'install.esd' -o -name 'boot.wim' \) 2>/dev/null | head -n 1)"; do
    if [[ -n "$candidate" && -f "$candidate" ]]; then
      case "$(basename "$candidate")" in
        install.wim|install.esd) INSTALL_WIM="$candidate" ;;
        boot.wim) BOOT_WIM="$candidate" ;;
      esac
    fi
  done
  for candidate in \
    "$work_iso/boot/bcd" \
    "$work_iso/efi/microsoft/boot/bcd"; do
    if [[ -f "$candidate" ]]; then
      BCD_STORE="$candidate"
      break
    fi
  done
  SFS_SOURCE="${INSTALL_WIM:-$BOOT_WIM}"
  SFS_NAME="$(basename "${SFS_SOURCE:-install.wim}")"
  export WINDOWS_INSTALL_WIM="$INSTALL_WIM"
  export WINDOWS_BOOT_WIM="$BOOT_WIM"
  export WINDOWS_BCD_STORE="$BCD_STORE"
}

adapter_sfs_write_path() {
  local work_iso="$1"
  adapter_resolve_sfs "$work_iso"
  if [[ -n "${INSTALL_WIM:-}" ]]; then
    printf '%s\n' "$INSTALL_WIM"
    return 0
  fi
  printf '%s\n' "$work_iso/sources/install.wim"
}

adapter_workdir_ready() {
  local work="$1"
  adapter_resolve_sfs "$work/iso"
  [[ -n "${SFS_SOURCE:-}" && -f "$SFS_SOURCE" ]] || return 1
  [[ -f "$work/rootfs/.forge-substrate-extracted" ]] || [[ -d "$work/rootfs/Windows" ]] || return 1
}

adapter_extract_rootfs() {
  local work_iso="$1"
  local rootfs_out="$2"
  adapter_resolve_sfs "$work_iso"
  if [[ -z "${SFS_SOURCE:-}" || ! -f "$SFS_SOURCE" ]]; then
    echo "ERROR: windows-wim-layout: no install.wim/install.esd/boot.wim found" >&2
    return 4
  fi

  mkdir -p "$rootfs_out"
  local index="${COGOS_WIM_INDEX:-1}"
  if command -v wimapply >/dev/null 2>&1; then
    echo "[windows-wim-layout] wimapply index=$index -> $rootfs_out"
    wimapply "$SFS_SOURCE" "$index" "$rootfs_out"
  elif command -v wimlib-imagex >/dev/null 2>&1; then
    echo "[windows-wim-layout] wimlib-imagex apply index=$index -> $rootfs_out"
    wimlib-imagex apply "$SFS_SOURCE" "$index" "$rootfs_out"
  else
    echo "ERROR: windows-wim-layout requires wimapply or wimlib-imagex on Linux/WSL" >&2
    echo "       Install: apt install wimtools  (provides wimapply)" >&2
    return 4
  fi

  mkdir -p "$rootfs_out/.forge/windows"
  [[ -n "${BOOT_WIM:-}" ]] && cp -f "$BOOT_WIM" "$rootfs_out/.forge/windows/boot.wim" 2>/dev/null || true
  [[ -n "${BCD_STORE:-}" ]] && cp -f "$BCD_STORE" "$rootfs_out/.forge/windows/bcd" 2>/dev/null || true

  # shellcheck source=inject-common.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../backends" && pwd)/inject-common.sh"
  inject_mark_extracted "$rootfs_out" "windows"
}
