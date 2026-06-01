#!/usr/bin/env bash
# Pre-release gate: full-runtime payload must install and first-boot cleanly.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

PAYLOAD="${COGOS_PAYLOAD:-${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}}"
if [[ ! -d "$PAYLOAD/opt/cogos" ]]; then
  PAYLOAD="${COGOS_PAYLOAD:-$WOLF_PAYLOAD}"
fi
# shellcheck source=lib/cogos-systemd-stack.sh
source "$SCRIPT_DIR/lib/cogos-systemd-stack.sh"

FAIL=0

check() {
  if eval "$2"; then
    echo "OK  $1"
  else
    echo "FAIL $1" >&2
    FAIL=1
  fi
}

echo "=== Full runtime release payload verify ==="
echo "Payload: $PAYLOAD"
echo ""

check "cogos-install" "test -x '$PAYLOAD/usr/local/bin/cogos-install'"
check "cogos-install-finish" "test -x '$PAYLOAD/usr/local/bin/cogos-install-finish'"
check "cognitive_init" "test -x '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "first-boot fast handoff in cognitive_init" \
  "grep -q first_boot_fast_handoff '$PAYLOAD/opt/cogos/bin/cognitive_init'"
check "cogos-daemon wrapper" "test -x '$PAYLOAD/usr/local/bin/cogos-daemon'"
check "cogos-first-boot helper" "test -x '$PAYLOAD/usr/local/bin/cogos-first-boot'"
check "firstboot.sh native launcher" "test -x '$PAYLOAD/usr/lib/cogos/firstboot.sh'"
check "cogos-firstboot.service ExecStart" \
  "grep -q '/usr/lib/cogos/firstboot.sh' '$PAYLOAD/etc/systemd/system/cogos-firstboot.service'"
check "systemd units not executable" "! test -x '$PAYLOAD/etc/systemd/system/cogos-governance.service'"
check "cogos-governance.service present" "test -f '$PAYLOAD/etc/systemd/system/cogos-governance.service'"
check "cogos-spine.service Wants governance" \
  "grep -q 'Wants=cogos-governance.service' '$PAYLOAD/etc/systemd/system/cogos-spine.service'"
check "boot hardening unit" "test -f '$PAYLOAD/etc/systemd/system/cogos-boot-hardening.service'"
check "boot hardening script" "test -x '$PAYLOAD/usr/lib/cogos/boot-service-hardening.sh'"
check "avahi boot drop-in" "test -f '$PAYLOAD/etc/systemd/system/avahi-daemon.service.d/cogos-boot.conf'"
check "boot stack artifact count = 4" "test '$(cogos_boot_stack_count)' -eq 4"
verify_cogos_boot_stack_present "$PAYLOAD" || FAIL=1
check "no blocking substrate drop-ins" \
  "! test -f '$PAYLOAD/etc/systemd/system/accounts-daemon.service.d/cogos-firstboot.conf'"
check "governance Wants substrate (not Requires)" \
  "grep -q 'Wants=dbus.service accounts-daemon.service' '$PAYLOAD/etc/systemd/system/cogos-governance.service'"
check "governance grace accounts-daemon" \
  "grep -q 'accounts-daemon.service' '$PAYLOAD/etc/cog/governance.json' && grep -q grace '$PAYLOAD/etc/cog/governance.json'"
check "governance-grace helper" "test -x '$PAYLOAD/usr/lib/cogos/governance-grace.sh'"
check "boot stack launchers" "test -x '$PAYLOAD/usr/lib/cogos/governance-daemon' && test -x '$PAYLOAD/usr/lib/cogos/spine' && test -x '$PAYLOAD/usr/lib/cogos/observer'"
check "boot stack launchers LF (no CRLF)" "! grep -l $'\r' '$PAYLOAD/usr/lib/cogos/'* 2>/dev/null | grep -q ."
check "boot stack systemd units LF (no CRLF)" "! find '$PAYLOAD/etc/systemd/system' -maxdepth 3 \( -name '*.service' -o -name '*.conf' \) -type f -exec grep -l $'\r' {} + 2>/dev/null | grep -q ."
check "no SysV 90cogos on payload" "! test -f '$PAYLOAD/etc/init.d/90cogos'"
check "cogos-runtime-start (legacy fallback)" "test -x '$PAYLOAD/usr/local/bin/cogos-runtime-start'"
WRAPPER_COUNT="$(find "$PAYLOAD/usr/local/bin" -maxdepth 1 -name 'cogos-*' -type f 2>/dev/null | wc -l)"
RUNTIME_PY_COUNT="$(find "$PAYLOAD/opt/cogos/runtime" -name '*.py' 2>/dev/null | wc -l)"
check "payload wrapper count >= 40" "test '$WRAPPER_COUNT' -ge 40"
check "runtime python modules >= 50" "test '$RUNTIME_PY_COUNT' -ge 50"
check "cognitive_runtime_family.json present" \
  "test -f '$PAYLOAD/opt/cogos/config/cognitive_runtime_family.json'"
check "nova_cortex.env present" \
  "test -f '$PAYLOAD/opt/cogos/config/nova_cortex.env'"
check "cog_runtime staged under runtime/src" \
  "test -d '$PAYLOAD/opt/cogos/runtime/src/cog_runtime'"
RUNTIME_ROOT="$PAYLOAD/opt/cogos/runtime"
SRC_ROOT="$RUNTIME_ROOT/src"
check "cogos_runtime_bridge importable from payload" \
  "PYTHONPATH='$RUNTIME_ROOT:$SRC_ROOT' python3 -c 'from src.cogos_runtime_bridge import family_spec; assert family_spec()[\"family_id\"]==\"nova.cortex\"'"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
check "cogos_runtime_bridge importable (repo)" \
  "PYTHONPATH='$REPO_ROOT' python3 -c 'from src.cogos_runtime_bridge import family_spec; assert family_spec()[\"family_id\"]'"

if (( FAIL )); then
  echo "" >&2
  echo "Full runtime payload checks FAILED. Sync payload from cache or rebuild." >&2
  exit 1
fi

echo ""
echo "=== All full runtime release checks passed ==="
