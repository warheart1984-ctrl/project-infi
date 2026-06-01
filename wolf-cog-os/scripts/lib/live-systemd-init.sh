#!/usr/bin/env bash
# Shared live-safe systemd init resolution (merged-usr aware).
set -euo pipefail

resolve_live_systemd_init() {
  local rootfs="$1"
  local candidate resolved

  for candidate in \
    "$rootfs/lib/systemd/systemd" \
    "$rootfs/usr/lib/systemd/systemd"; do
    if [[ -x "$candidate" ]]; then
      resolved="$(readlink -f "$candidate" 2>/dev/null || echo "$candidate")"
      printf '%s\n' "$resolved"
      return 0
    fi
  done
  return 1
}

resolve_init_link_target_in_rootfs() {
  local rootfs="$1"
  local init_link="$2"
  local raw target

  [[ -e "$init_link" ]] || return 1
  if [[ ! -L "$init_link" ]]; then
    readlink -f "$init_link" 2>/dev/null || echo "$init_link"
    return 0
  fi

  raw="$(readlink "$init_link")"
  if [[ "$raw" == /* ]]; then
    target="$rootfs$raw"
  else
    target="$(cd "$(dirname "$init_link")" && cd "$(dirname "$raw")" && pwd)/$(basename "$raw")"
  fi
  readlink -f "$target" 2>/dev/null || echo "$target"
}

same_init_path() {
  local left="$1"
  local right="$2"
  local left_res right_res

  [[ -n "$left" && -n "$right" ]] || return 1
  left_res="$(readlink -f "$left" 2>/dev/null || echo "$left")"
  right_res="$(readlink -f "$right" 2>/dev/null || echo "$right")"
  [[ "$left_res" == "$right_res" ]]
}

same_init_in_rootfs() {
  local rootfs="$1"
  local init_link="$2"
  local systemd_bin="$3"
  local resolved

  resolved="$(resolve_init_link_target_in_rootfs "$rootfs" "$init_link")" || return 1
  same_init_path "$resolved" "$systemd_bin"
}

restore_live_systemd_init_links() {
  local rootfs="$1"
  local systemd_bin

  systemd_bin="$(resolve_live_systemd_init "$rootfs")" || return 1

  rm -f "$rootfs/usr/sbin/init"
  ln -s ../lib/systemd/systemd "$rootfs/usr/sbin/init"
  if [[ -d "$rootfs/sbin" ]]; then
    rm -f "$rootfs/sbin/init"
    ln -s ../lib/systemd/systemd "$rootfs/sbin/init"
  fi

  same_init_in_rootfs "$rootfs" "$rootfs/usr/sbin/init" "$systemd_bin"
}

verify_live_systemd_init_links() {
  local rootfs="$1"
  local systemd_bin
  local usr_init="$rootfs/usr/sbin/init"
  local sbin_init="$rootfs/sbin/init"

  systemd_bin="$(resolve_live_systemd_init "$rootfs")" || return 1
  same_init_in_rootfs "$rootfs" "$usr_init" "$systemd_bin" || return 1

  if [[ -e "$rootfs/sbin" ]]; then
    same_init_in_rootfs "$rootfs" "$sbin_init" "$systemd_bin" || return 1
  fi
  return 0
}
