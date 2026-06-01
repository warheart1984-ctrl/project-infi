#!/usr/bin/env bash
# Stage Wolf CoG OS runtime + d-i hook files on ISO /install/ (outside squashfs).
set -euo pipefail

# shellcheck source=lib/cogos-systemd-stack.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/cogos-systemd-stack.sh"

stage_di_copy_stack_artifact() {
  local rootfs="$1"
  local stage="$2"
  local script_dir="$3"
  local rel="$4"
  local name="${rel#etc/systemd/system/}"
  local dst="$stage/etc/systemd/system/$name"
  mkdir -p "$(dirname "$dst")"
  if [[ -f "$rootfs/etc/systemd/system/$name" ]]; then
    cp -a "$rootfs/etc/systemd/system/$name" "$dst"
  elif [[ -f "$script_dir/../payload/etc/systemd/system/$name" ]]; then
    cp -a "$script_dir/../payload/etc/systemd/system/$name" "$dst"
  fi
  chmod 644 "$dst" 2>/dev/null || true
}

stage_di_copy_launcher() {
  local rootfs="$1"
  local stage="$2"
  local script_dir="$3"
  local name="$4"
  if [[ -f "$rootfs/usr/lib/cogos/$name" ]]; then
    cp -a "$rootfs/usr/lib/cogos/$name" "$stage/usr/lib/cogos/$name"
  elif [[ -f "$script_dir/../payload/usr/lib/cogos/$name" ]]; then
    cp -a "$script_dir/../payload/usr/lib/cogos/$name" "$stage/usr/lib/cogos/$name"
  fi
  chmod +x "$stage/usr/lib/cogos/$name" 2>/dev/null || true
}

stage_di_iso_payload() {
  local rootfs="${1:-${WORK:?}/rootfs}"
  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local iso_install="${WORK}/iso/install/wolf-cog-os"
  local preseed_src="$script_dir/../payload-iso/install/wolf-cog-os.preseed"
  local wifi_probe_src="$script_dir/../payload-iso/install/cogos-di-wifi-probe.sh"
  local netcfg_dispatch_src="$script_dir/../payload-iso/install/cogos-di-netcfg-dispatch.sh"
  local late_src="$script_dir/../payload-iso/install/cogos-di-late-command.sh"
  local stage="${WORK}/tmp/cogos-di-runtime-stage"

  [[ -d "$rootfs/opt/cogos" ]] || {
    echo "ERROR: stage_di_iso_payload: missing $rootfs/opt/cogos" >&2
    return 1
  }

  mkdir -p "$iso_install"
  cp -f "$preseed_src" "${WORK}/iso/install/wolf-cog-os.preseed"
  cp -f "$wifi_probe_src" "$iso_install/cogos-di-wifi-probe.sh"
  cp -f "$netcfg_dispatch_src" "$iso_install/cogos-di-netcfg-dispatch.sh"
  cp -f "$late_src" "$iso_install/cogos-di-late-command.sh"
  chmod +x "$iso_install/cogos-di-wifi-probe.sh" "$iso_install/cogos-di-netcfg-dispatch.sh" "$iso_install/cogos-di-late-command.sh"
  cp -f "$rootfs/usr/local/bin/cogos-install-finish" "$iso_install/cogos-install-finish"
  chmod +x "$iso_install/cogos-di-late-command.sh" "$iso_install/cogos-install-finish"

  rm -rf "$stage"
  mkdir -p "$stage/opt/cogos" "$stage/usr/local/bin" "$stage/usr/lib/cogos" \
    "$stage/etc/systemd/system" "$stage/etc/systemd/system/accounts-daemon.service.d" \
    "$stage/etc/cog" "$stage/etc/cogos"
  rsync -a "$rootfs/opt/cogos/" "$stage/opt/cogos/"
  for bin in "$rootfs"/usr/local/bin/cogos-*; do
    [[ -f "$bin" ]] || continue
    cp -a "$bin" "$stage/usr/local/bin/"
  done

  for rel in "${COGOS_BOOT_STACK_UNITS[@]}"; do
    stage_di_copy_stack_artifact "$rootfs" "$stage" "$script_dir" "$rel"
  done

  for launcher in firstboot.sh governance-grace.sh governance-daemon spine observer; do
    stage_di_copy_launcher "$rootfs" "$stage" "$script_dir" "$launcher"
  done

  if [[ -f "$rootfs/etc/cog/governance.json" ]]; then
    cp -a "$rootfs/etc/cog/governance.json" "$stage/etc/cog/governance.json"
  elif [[ -f "$script_dir/../payload/etc/cog/governance.json" ]]; then
    cp -a "$script_dir/../payload/etc/cog/governance.json" "$stage/etc/cog/governance.json"
  fi
  if [[ -f "$stage/etc/cog/governance.json" ]]; then
    cp -a "$stage/etc/cog/governance.json" "$stage/etc/cogos/governance.json"
  fi

  local wrapper_count=0
  wrapper_count="$(find "$stage/usr/local/bin" -maxdepth 1 -name 'cogos-*' -type f | wc -l)"
  [[ -x "$stage/usr/lib/cogos/governance-grace.sh" ]] || {
    echo "ERROR: stage_di_iso_payload: /usr/lib/cogos/governance-grace.sh missing" >&2
    return 1
  }
  [[ -x "$stage/usr/lib/cogos/firstboot.sh" ]] || {
    echo "ERROR: stage_di_iso_payload: /usr/lib/cogos/firstboot.sh missing" >&2
    return 1
  }
  [[ -f "$stage/etc/cog/governance.json" ]] || {
    echo "ERROR: stage_di_iso_payload: /etc/cog/governance.json missing" >&2
    return 1
  }
  verify_cogos_boot_stack_present "$stage" || {
    echo "ERROR: stage_di_iso_payload: boot stack incomplete (need $(cogos_boot_stack_count) artifacts)" >&2
    return 1
  }
  if [[ "$wrapper_count" -lt 40 ]]; then
    echo "ERROR: stage_di_iso_payload: only $wrapper_count cogos-* wrappers staged (need >= 40)" >&2
    return 1
  fi

  tar -C "$stage" -cf "$iso_install/runtime.tar" .
  rm -rf "$stage"

  echo "[4d/9] Debian installer payload on ISO: runtime.tar ($(du -h "$iso_install/runtime.tar" | awk '{print $1}'), $wrapper_count wrappers, boot stack x$(cogos_boot_stack_count))"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  WORK="${COGOS_WORK:?}"
  # shellcheck source=paths.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/paths.sh"
  stage_di_iso_payload "${1:-$WORK/rootfs}"
fi
