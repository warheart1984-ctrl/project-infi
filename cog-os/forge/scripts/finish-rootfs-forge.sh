#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
# shellcheck source=lib/run-bash-script.sh
source <(sed 's/\r$//' "$SCRIPT_DIR/lib/run-bash-script.sh")
PROFILE="${COG_PROFILE:-daily-driver}"
EFFECTIVE="${COG_EFFECTIVE_ROOTFS:-/var/tmp/cog-os/rootfs-${PROFILE}}"

if [[ ! -d "$EFFECTIVE/usr" ]]; then
  echo "missing rootfs tree: $EFFECTIVE" >&2
  exit 1
fi

HOST_OVERLAY="$REPO_ROOT/cog-os/host/rootfs"
if [[ -d "$HOST_OVERLAY" ]]; then
  rsync -a "$HOST_OVERLAY/" "$EFFECTIVE/"
  chmod +x "$EFFECTIVE/etc/rc.sh" "$EFFECTIVE/etc/cog/services/"*.sh 2>/dev/null || true
fi

bash "$SCRIPT_DIR/lib/render-init-conf.sh" --profile "$PROFILE" --output "$EFFECTIVE/etc/init.conf"
chmod 0644 "$EFFECTIVE/etc/init.conf"

COG_REPO_ROOT="$REPO_ROOT" COG_PAYLOAD_UL="${COG_PAYLOAD_UL:-0}" \
  COG_PAYLOAD_USL_LIFTED="${COG_PAYLOAD_USL_LIFTED:-0}" \
  COG_PROFILE="$PROFILE" \
  run_bash_script "$SCRIPT_DIR/lib/payload-stage.sh" "$EFFECTIVE"

if [[ "$PROFILE" == "daily-driver" ]]; then
  bash "$SCRIPT_DIR/lib/install-daily-driver-session.sh" "$EFFECTIVE"
fi

bash "$SCRIPT_DIR/lib/emit-profile-attestation.sh" --profile "$PROFILE" --rootfs "$EFFECTIVE"

echo "Nova NorthStar CoG OS rootfs forge complete: $EFFECTIVE (profile=$PROFILE)"
