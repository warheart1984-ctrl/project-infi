#!/usr/bin/env bash
set -euo pipefail

network_plan() {
  emit_plan_line "Configure network defaults"
  emit_plan_line "  mode: NetworkManager + DHCP fallback"
}

network_apply() {
  network_plan

  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    [[ -f "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf" ]] && cp -a "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf" "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf.cogos-installer.bak" || true
    [[ -f "$TARGET_MOUNT_ROOT/etc/network/interfaces" ]] && cp -a "$TARGET_MOUNT_ROOT/etc/network/interfaces" "$TARGET_MOUNT_ROOT/etc/network/interfaces.cogos-installer.bak" || true
  fi

  run_cmd mkdir -p "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d"
  run_cmd bash -lc "cat > '$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf' <<'EOF'
[main]
plugins=ifupdown,keyfile

[ifupdown]
managed=true
EOF"

  run_cmd bash -lc "cat > '$TARGET_MOUNT_ROOT/etc/network/interfaces' <<'EOF'
auto lo
iface lo inet loopback
EOF"
}

network_rollback() {
  if [[ -f "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf.cogos-installer.bak" ]]; then
    run_cmd mv -f "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf.cogos-installer.bak" "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf"
  else
    safe_remove "$TARGET_MOUNT_ROOT/etc/NetworkManager/conf.d/10-cogos-defaults.conf"
  fi

  if [[ -f "$TARGET_MOUNT_ROOT/etc/network/interfaces.cogos-installer.bak" ]]; then
    run_cmd mv -f "$TARGET_MOUNT_ROOT/etc/network/interfaces.cogos-installer.bak" "$TARGET_MOUNT_ROOT/etc/network/interfaces"
  else
    safe_remove "$TARGET_MOUNT_ROOT/etc/network/interfaces"
  fi
}
