#!/usr/bin/env bash
set -euo pipefail
WORK="${1:-/home/nullzero/.cogos-forge-work/scratch}"
forge_log_step() { printf '%s\n' "$*" >&2; }

chmod_existing() {
  local f
  for f in "$@"; do
    if [[ -e "$f" ]]; then
      forge_log_step "chmod: $f"
      chmod +x "$f"
    fi
  done
}

forge_log_step "[4c+] Setting CoGOS binary modes"
chmod_existing \
  "$WORK/rootfs/opt/cogos/bin/cognitive_init" \
  "$WORK/rootfs/opt/cogos/bin/cogos_shell" \
  "$WORK/rootfs/opt/cogos/bin/cogos_boot.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_daemon.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_first_run.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_supernova.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_daily_driver.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_manifest.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_install_proof.py" \
  "$WORK/rootfs/opt/cogos/bin/cogos_master_boot.py"
forge_log_step "[4c+] Binary modes done"
forge_log_step "[4d/9] Branding live session (probe)"
