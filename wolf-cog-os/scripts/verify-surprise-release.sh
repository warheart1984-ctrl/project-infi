#!/usr/bin/env bash
# Pre-release gate: surprise ISO payload must boot on first reboot without manual fixes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

PAYLOAD="${COGOS_PAYLOAD:-${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}}"
if [[ ! -d "$PAYLOAD/opt/cogos" ]]; then
  PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
fi
FAIL=0

check() {
  if eval "$2"; then
    echo "OK  $1"
  else
    echo "FAIL $1" >&2
    FAIL=1
  fi
}

echo "=== Surprise release payload verify ==="
echo "Payload: $PAYLOAD"
echo ""

check "cogos-install-finish" "test -x '$PAYLOAD/usr/local/bin/cogos-install-finish'"
check "cogos-first-boot" "test -x '$PAYLOAD/usr/local/bin/cogos-first-boot'"
check "cognitive_init" "test -x '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "first-boot fast handoff in cognitive_init" \
  "grep -q first_boot_fast_handoff '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "first-boot service after graphical.target" \
  "grep -q 'WantedBy=graphical.target' '$PAYLOAD/etc/systemd/system/cogos-first-boot.service'"
check "no boot block Before=multi-user.target" \
  "! grep -q 'Before=multi-user.target' '$PAYLOAD/etc/systemd/system/cogos-first-boot.service'"

if [[ -f "$PAYLOAD/etc/calamares/modules/shellprocess@cogos-finish.conf" ]]; then
  echo "OK  calamares module file in payload (build also patches settings.conf)"
else
  echo "NOTE calamares module is applied at ISO build time via patch_calamares_surprise.sh"
fi

if (( FAIL )); then
  echo "" >&2
  echo "Release payload checks FAILED. Sync payload from cache or rebuild." >&2
  exit 1
fi

echo ""
echo "=== All surprise release checks passed ==="
