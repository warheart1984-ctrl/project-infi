#!/usr/bin/env bash
# Slice 1 admission: metal rootfs attestation → QEMU contract-boot → Megaton phase-1 live.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COG_OS_DIR="$REPO_ROOT/cog-os"

PROFILE="${COG_PROFILE:-metal}"
ROOTFS="${COG_ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-$PROFILE}"
SKIP_ROOTFS=0
MEGATON_ROUNDS="${USL_MEGATON_ROUNDS:-${COG_USL_MEGATON_ROUNDS:-20}}"

ATTESTATION_OUT="${COG_ATTESTATION_OUT:-$REPO_ROOT/artifacts/cog-os/profile-attestation-$PROFILE.json}"
CONTRACT_BOOT="$REPO_ROOT/ci-artifacts/qemu-contract-boot.json"
MEGATON_REPORT="$REPO_ROOT/ci-artifacts/usl_megaton_chaos_report.json"
ADMIT_OUT="$REPO_ROOT/ci-artifacts/usl-slice1-admit.json"

usage() {
  cat <<EOF
Usage: $0 [--profile metal] [--rootfs PATH] [--skip-rootfs] [--megaton-rounds N]

Slice 1 admission (metal): build rootfs → profile attestation → QEMU contract-boot
with --usl-megaton (phase 1, --require-live against guest :8766).

Requires Linux/WSL with KVM, qemu-system-x86_64, curl, python3, make.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --rootfs) ROOTFS="$2"; shift 2 ;;
    --skip-rootfs) SKIP_ROOTFS=1; shift ;;
    --megaton-rounds) MEGATON_ROUNDS="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ "$PROFILE" != "metal" ]]; then
  echo "usl-slice1-admit: profile must be metal (got $PROFILE)" >&2
  exit 1
fi

ROOTFS="${COG_ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-$PROFILE}"
ATTESTATION_OUT="${COG_ATTESTATION_OUT:-$REPO_ROOT/artifacts/cog-os/profile-attestation-$PROFILE.json}"

log() { echo "[usl-slice1-admit] $*" >&2; }

write_admit_json() {
  local admitted="$1"
  local tier_a="$2"
  local tier_b="$3"
  local tier_c="$4"
  local reason="${5:-}"
  mkdir -p "$(dirname "$ADMIT_OUT")"
  python3 - "$ADMIT_OUT" "$admitted" "$tier_a" "$tier_b" "$tier_c" "$reason" \
    "$PROFILE" "$ROOTFS" "$ATTESTATION_OUT" "$CONTRACT_BOOT" "$MEGATON_REPORT" <<'PY'
import json, sys
from datetime import datetime, timezone

(
    out_path,
    admitted,
    tier_a,
    tier_b,
    tier_c,
    reason,
    profile,
    rootfs,
    attestation,
    contract_boot,
    megaton_report,
) = sys.argv[1:12]

doc = {
    "schema": "usl-slice1-admit.v1",
    "profile": profile,
    "admitted": admitted == "true",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "tiers": {
        "A_static": {"pass": tier_a == "true", "attestation": attestation},
        "B_boot": {"pass": tier_b == "true", "qemu_contract_boot": contract_boot},
        "C_megaton_live": {"pass": tier_c == "true", "megaton_report": megaton_report},
    },
    "rootfs": rootfs,
    "megaton_rounds": int(__import__("os").environ.get("USL_MEGATON_ROUNDS", __import__("os").environ.get("COG_USL_MEGATON_ROUNDS", "20"))),
}
if reason:
    doc["reason"] = reason

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")
print(out_path)
PY
}

fail_admit() {
  local tier_a="${1:-false}"
  local tier_b="${2:-false}"
  local tier_c="${3:-false}"
  local reason="$4"
  write_admit_json false "$tier_a" "$tier_b" "$tier_c" "$reason"
  log "NOT ADMITTED: $reason"
  exit 1
}

cd "$REPO_ROOT"

if [[ "$SKIP_ROOTFS" -eq 0 ]]; then
  log "Tier A: building rootfs (COG_PROFILE=$PROFILE)"
  make cog-rootfs COG_PROFILE="$PROFILE"
else
  log "Tier A: skip rootfs build (--skip-rootfs)"
fi

if [[ ! -d "$ROOTFS/usr" ]]; then
  fail_admit false false false "rootfs missing: $ROOTFS"
fi

log "Tier A: profile attestation"
bash "$COG_OS_DIR/forge/scripts/lib/emit-profile-attestation.sh" \
  --profile "$PROFILE" --rootfs "$ROOTFS" --output "$ATTESTATION_OUT"

tier_a_ok=0
if python3 - "$ATTESTATION_OUT" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
gates = doc.get("gates") or {}
ok = gates.get("usl_health_200") is True
print("true" if ok else "false")
sys.exit(0 if ok else 1)
PY
then
  tier_a_ok=1
  log "Tier A: PASS (gates.usl_health_200=true)"
else
  fail_admit false false false "gates.usl_health_200 != true in $ATTESTATION_OUT"
fi

log "Tier B+C: QEMU contract-boot + Megaton phase-1 (--require-live)"
export USL_MEGATON_ROUNDS="$MEGATON_ROUNDS"
export COG_USL_MEGATON_ROUNDS="$MEGATON_ROUNDS"
if ! COG_ROOTFS="$ROOTFS" bash "$COG_OS_DIR/scripts/test/qemu-smoke.sh" \
  --contract --contract-boot --usl-megaton --profile "$PROFILE"; then
  fail_admit true false false "qemu contract-boot or usl-megaton failed"
fi

tier_b_ok=0
tier_c_ok=0
if [[ -f "$CONTRACT_BOOT" ]]; then
  read -r tier_b_ok tier_c_ok < <(python3 - "$CONTRACT_BOOT" "$MEGATON_REPORT" <<'PY'
import json, sys

boot_path, megaton_path = sys.argv[1:3]
def _truthy(v):
    return v in (True, 1, "1", "true")

boot = json.load(open(boot_path, encoding="utf-8"))
boot_ok = (
    boot.get("status") == "pass"
    and _truthy(boot.get("usl_health_200"))
    and _truthy(boot.get("usl_serial_ok"))
)
megaton_ok = False
if boot.get("usl_megaton_skipped"):
    megaton_ok = False
elif _truthy(boot.get("usl_megaton_pass")):
    megaton_ok = True
if megaton_path and __import__("pathlib").Path(megaton_path).is_file():
    m = json.load(open(megaton_path, encoding="utf-8")).get("summary") or {}
    megaton_ok = (
        _truthy(m.get("pass"))
        and m.get("unexpected_failures", 1) == 0
        and m.get("crashes", 1) == 0
        and m.get("health_skips", -1) == 0
        and _truthy(m.get("require_live"))
    )
print("1" if boot_ok else "0", "1" if megaton_ok else "0")
PY
  )
fi

if [[ "$tier_b_ok" -ne 1 ]]; then
  fail_admit true false false "qemu-contract-boot: status!=pass or usl_health_200/usl_serial_ok false"
fi
if [[ "$tier_c_ok" -ne 1 ]]; then
  fail_admit true true false "megaton phase-1 live: pass=false or health_skips>0"
fi

write_admit_json true true true true ""
log "Slice 1 ADMITTED -> $ADMIT_OUT"
cat "$ADMIT_OUT"
