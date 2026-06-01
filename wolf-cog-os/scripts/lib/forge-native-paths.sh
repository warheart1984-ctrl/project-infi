#!/usr/bin/env bash
# Redirect Forge work/rootfs paths off DrvFs (/mnt/*) when debootstrap/unsquashfs need native Linux fs.
set -euo pipefail

forge_path_fstype() {
  local path="$1"
  local parent="${path%/*}"
  [[ -n "$parent" && -d "$parent" ]] || parent="$path"
  df -T "$parent" 2>/dev/null | tail -1 | awk '{print $2}'
}

forge_repo_on_drvfs() {
  local repo="${REPO_ROOT:-.}"
  [[ "$(forge_path_fstype "$repo")" == "9p" ]]
}

forge_path_on_drvfs() {
  [[ "$(forge_path_fstype "$1")" == "9p" ]]
}

forge_invoke_user_home() {
  local u="${SUDO_USER:-${COGOS_BUILD_USER:-${USER:-}}}"
  if [[ -n "$u" && "$u" != "root" ]]; then
    getent passwd "$u" 2>/dev/null | cut -d: -f6
    return 0
  fi
  printf '%s\n' "${HOME:-/tmp}"
}

# When repo or chosen rootfs path sits on 9p, force native ext4 work under invoking user's $HOME.
forge_apply_native_work_paths() {
  local candidate_out="${1:-${COGOS_ROOTFS_OUT:-${WOLF_ROOTFS_OUT:-}}}"
  if [[ -z "$candidate_out" ]]; then
    candidate_out="${REPO_ROOT:-.}/wolf-cog-os/build/rootfs"
  fi

  if ! forge_repo_on_drvfs && ! forge_path_on_drvfs "$candidate_out"; then
    return 0
  fi

  local native_base tag_slug
  native_base="$(forge_invoke_user_home)/.cogos-forge-work"
  tag_slug="${COGOS_TAG:-forge}"
  tag_slug="${tag_slug//[^A-Za-z0-9]/-}"

  export COGOS_WORK="${COGOS_WORK:-$native_base/scratch}"
  export COGOS_ROOTFS_OUT="${COGOS_ROOTFS_OUT:-$native_base/rootfs-forge}"
  export COGOS_ROOTFS_WORK="${COGOS_ROOTFS_WORK:-$native_base/rootfs-stage}"
  export COGOS_ROOTFS_SRC="${COGOS_ROOTFS_SRC:-$COGOS_ROOTFS_OUT}"

  echo "[forge] DrvFs repo/output detected; using native paths:"
  echo "[forge]   COGOS_WORK=$COGOS_WORK"
  echo "[forge]   COGOS_ROOTFS_OUT=$COGOS_ROOTFS_OUT"
}

forge_log_rootfs_filesystem() {
  local path="$1"
  local label="$2"
  echo "[forge] $label=$path (fs=$(forge_path_fstype "$path"))"
}
