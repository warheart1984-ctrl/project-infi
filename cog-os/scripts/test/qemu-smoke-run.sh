#!/usr/bin/env bash
# QEMU smoke / contract checks for Nova NorthStar CoG OS (cog-os/).
set -euo pipefail
export PATH="/usr/sbin:/sbin:${PATH:-/usr/local/bin:/usr/bin:/bin}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COG_OS_DIR="$REPO_ROOT/cog-os"
HOST_DIR="$COG_OS_DIR/host"
# shellcheck source=../../forge/scripts/lib/resolve-rootfs.sh
source "$COG_OS_DIR/forge/scripts/lib/resolve-rootfs.sh"

PROFILE="${COG_PROFILE:-metal}"
CONTRACT=0
CONTRACT_BOOT=0
BUILD=0
USL_MEGATON=0
USL_SLICE2=0
ROOTFS=""
ROOTFS_ARTIFACT=""
TIMEOUT_SEC="${COG_QEMU_TIMEOUT:-}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}"
GATEKEEPER_MARK="Nova NorthStar CoG OS gatekeeper PID1 starting"
AAIS_PORT="${COG_AAIS_PORT:-8765}"
USL_PORT="${COG_USL_PORT:-8766}"
OPERATOR_PORT="${COG_OPERATOR_PORT:-8000}"
MEGATON_REPORT="$ARTIFACT_DIR/usl_megaton_chaos_report.json"

usage() {
  echo "usage: qemu-smoke.sh [--profile metal|daily-driver|usl-lifted-guest] [--build] [--rootfs PATH]" >&2
  echo "       qemu-smoke.sh --contract [--contract-boot] [--usl-megaton] [--usl-slice2] [--profile NAME]" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --build) BUILD=1; shift ;;
    --rootfs) ROOTFS="$2"; shift 2 ;;
    --contract) CONTRACT=1; shift ;;
    --contract-boot) CONTRACT=1; CONTRACT_BOOT=1; shift ;;
    --usl-megaton) USL_MEGATON=1; shift ;;
    --usl-slice2) USL_SLICE2=1; USL_MEGATON=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown: $1" >&2; usage ;;
  esac
done

if [[ -z "$TIMEOUT_SEC" ]]; then
  case "$PROFILE" in
    daily-driver) TIMEOUT_SEC=600 ;;
    *) TIMEOUT_SEC=120 ;;
  esac
fi

mkdir -p "$ARTIFACT_DIR"
CONTRACT_JSON_STATIC="$ARTIFACT_DIR/qemu-contract-static.json"
CONTRACT_JSON_BOOT="$ARTIFACT_DIR/qemu-contract-boot.json"
CONTRACT_JSON="$ARTIFACT_DIR/qemu-contract.json"
CONTRACT_LOG="$ARTIFACT_DIR/qemu-contract.log"
: >"$CONTRACT_LOG"

log() { echo "$@" >>"$CONTRACT_LOG"; echo "$@" >&2; }

write_contract_json() {
  local out_path="$1"
  local mode="$2" status="$3" checks_json="$4"
  local extra="${5:-}"
  python3 - "$out_path" "$mode" "$status" "$PROFILE" "$TIMEOUT_SEC" "$checks_json" "$extra" <<'PY'
import json, sys
path, mode, status, profile, timeout, checks_json, extra = sys.argv[1:8]
checks = json.loads(checks_json) if checks_json else []
doc = {
    "mode": mode,
    "status": status,
    "profile": profile,
    "timeout_sec": int(timeout),
    "checks": checks,
}
if extra:
    doc.update(json.loads(extra))
with open(path, "w", encoding="utf-8") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")
PY
}

run_static_contract() {
  local failed=0
  local -a checks=()

  check() {
    local name="$1"
    shift
    if "$@"; then
      checks+=("$name")
      log "PASS: $name"
    else
      log "FAIL: $name"
      failed=1
    fi
  }

  check "init.c gatekeeper string" grep -q "$GATEKEEPER_MARK" "$HOST_DIR/src/init.c"
  check "rc.sh contract emitter" grep -q 'event":"contract"' "$HOST_DIR/rootfs/etc/rc.sh"
  check "platform.sh bash -n" bash -n "$HOST_DIR/rootfs/etc/cog/services/platform.sh"
  check "hardware.sh bash -n" bash -n "$HOST_DIR/rootfs/etc/cog/services/hardware.sh"
  check "aais.sh bash -n" bash -n "$HOST_DIR/rootfs/etc/cog/services/aais.sh"
  check "usl.sh bash -n" bash -n "$HOST_DIR/rootfs/etc/cog/services/usl.sh"
  check "profile metal.yaml" test -f "$COG_OS_DIR/forge/profiles/metal.yaml"
  check "profile daily-driver.yaml" test -f "$COG_OS_DIR/forge/profiles/daily-driver.yaml"
  check "profile usl-lifted-guest.yaml" test -f "$COG_OS_DIR/forge/profiles/usl-lifted-guest.yaml"
  check "profile-loader.sh" test -x "$COG_OS_DIR/forge/scripts/lib/profile-loader.sh"

  local checks_json
  checks_json="$(printf '%s\n' "${checks[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"

  if [[ "$failed" -eq 0 ]]; then
    write_contract_json "$CONTRACT_JSON_STATIC" "static" "pass" "$checks_json"
    cp -f "$CONTRACT_JSON_STATIC" "$CONTRACT_JSON"
    log "static contract: pass -> $CONTRACT_JSON_STATIC"
    return 0
  fi
  write_contract_json "$CONTRACT_JSON_STATIC" "static" "fail" "$checks_json"
  cp -f "$CONTRACT_JSON_STATIC" "$CONTRACT_JSON"
  log "static contract: fail"
  return 1
}

materialize_rootfs_disk() {
  local img="$ARTIFACT_DIR/rootfs-${PROFILE}.img"
  local size_mb="${COG_ROOTFS_IMG_MB:-}"
  local source_root="$ROOTFS"
  local build_root="$ROOTFS"

  # mkfs.ext4 -d is extremely slow when the image lives on drvfs (/mnt/*).
  if [[ "${img}" == /mnt/* ]] && [[ -z "${COG_ROOTFS_DISK:-}" ]]; then
    mkdir -p /var/tmp/cog-os
    img="/var/tmp/cog-os/rootfs-${PROFILE}.img"
    log "boot: using native disk image path $img (avoid drvfs mkfs slowness)"
  fi
  if [[ -n "${COG_ROOTFS_DISK:-}" ]]; then
    img="$COG_ROOTFS_DISK"
  fi

  if [[ -f "$img" ]]; then
    local rootfs_stamp="$source_root/.cog-build-stamp"
    if [[ -f "$rootfs_stamp" && "$rootfs_stamp" -nt "$img" ]]; then
      log "boot: reuse disk image $img"
      echo "$img"
      return 0
    fi
  fi

  if [[ -z "$size_mb" ]]; then
    local used_kb headroom_kb
    used_kb="$(du -sk "$source_root" 2>/dev/null | awk '{print $1}')"
    headroom_kb=$((used_kb / 4 + 524288))
    size_mb=$(((used_kb + headroom_kb + 1023) / 1024))
    if [[ "$size_mb" -lt 2048 ]]; then
      size_mb=2048
    fi
  fi

  log "boot: building ext4 disk image (${size_mb} MB) from $source_root"
  rm -f "$img"
  qemu-img create -f raw "$img" "${size_mb}M" >/dev/null

  if mkfs.ext4 -F -d "$build_root" "$img" >>"$CONTRACT_LOG" 2>&1; then
    log "boot: mkfs.ext4 -d populated $img"
    echo "$img"
    return 0
  fi

  log "boot: mkfs.ext4 -d failed; staging copy on native filesystem"
  build_root="$ARTIFACT_DIR/rootfs-staging-copy-${PROFILE}"
  rm -rf "$build_root"
  mkdir -p "$build_root"
  rsync -a "$source_root/" "$build_root/"

  if mkfs.ext4 -F -d "$build_root" "$img" >>"$CONTRACT_LOG" 2>&1; then
    log "boot: mkfs.ext4 -d populated $img from staging copy"
    echo "$img"
    return 0
  fi

  log "boot: mkfs.ext4 -d unavailable; falling back to loop mount"
  local mount_dir
  mount_dir="$(mktemp -d "${TMPDIR:-/tmp}/cog-rootfs-mnt.XXXXXX")"
  mkfs.ext4 -F "$img" >>"$CONTRACT_LOG" 2>&1

  populate_via_loop() {
    local loop_dev="$1"
    mount "$loop_dev" "$mount_dir"
    rsync -a "$build_root/" "$mount_dir/"
    sync
    umount "$mount_dir"
    losetup -d "$loop_dev"
  }

  if command -v losetup >/dev/null 2>&1; then
    local loop_dev=""
    if loop_dev="$(losetup --find --show "$img" 2>>"$CONTRACT_LOG")"; then
      populate_via_loop "$loop_dev" && {
        rmdir "$mount_dir" 2>/dev/null || true
        echo "$img"
        return 0
      }
      losetup -d "$loop_dev" 2>/dev/null || true
    fi
    if command -v sudo >/dev/null 2>&1; then
      loop_dev="$(sudo losetup --find --show "$img")"
      sudo bash -c "$(declare -f populate_via_loop); populate_via_loop '$loop_dev'" || true
      sudo losetup -d "$loop_dev" 2>/dev/null || true
      if [[ -f "$img" ]]; then
        rmdir "$mount_dir" 2>/dev/null || true
        log "boot: loop mount populated $img (sudo)"
        echo "$img"
        return 0
      fi
    fi
  fi

  log "FAIL: cannot populate disk (need mkfs.ext4 -d or losetup+mount)"
  rmdir "$mount_dir" 2>/dev/null || true
  return 1
}

poll_http_200() {
  local url="$1"
  local limit="${2:-30}"
  local elapsed=0
  local code="000"
  while [[ "$elapsed" -lt "$limit" ]]; do
    code="$(curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 "$url" 2>/dev/null || true)"
    code="${code:-000}"
    if [[ "$code" == "200" ]]; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  echo "$code"
  return 1
}

poll_aais_health() {
  local code
  if poll_http_200 "http://127.0.0.1:${AAIS_PORT}/health" "${COG_AAIS_POLL_SEC:-45}"; then
    log "boot: AAIS /health HTTP 200"
    return 0
  fi
  code="$(curl -sf -o /dev/null -w '%{http_code}' "http://127.0.0.1:${AAIS_PORT}/health" 2>/dev/null || echo "000")"
  log "boot: AAIS /health not ready (last HTTP $code)"
  return 1
}

poll_usl_health() {
  local require_broker="${1:-0}"
  local elapsed=0
  local limit="${COG_USL_POLL_SEC:-90}"
  local body code="000"
  while [[ "$elapsed" -lt "$limit" ]]; do
    body="$(curl -sf "http://127.0.0.1:${USL_PORT}/health" 2>/dev/null || true)"
    if [[ -n "$body" ]]; then
      if [[ "$require_broker" -eq 1 ]]; then
        if python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d.get("phase")==2 and d.get("broker")=="ok" else 1)' "$body" 2>/dev/null; then
          log "boot: USL /health phase=2 broker=ok"
          echo "$body"
          return 0
        fi
      elif python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d.get("status") in ("ok","degraded") else 1)' "$body" 2>/dev/null; then
        log "boot: USL /health ok"
        echo "$body"
        return 0
      fi
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  log "boot: USL /health not ready on :${USL_PORT}"
  return 1
}

poll_operator_ui() {
  local path="${COG_OPERATOR_PATH:-/app/}"
  if poll_http_200 "http://127.0.0.1:${OPERATOR_PORT}${path}" "${COG_OPERATOR_POLL_SEC:-60}"; then
    log "boot: operator UI HTTP 200 at :${OPERATOR_PORT}${path}"
    return 0
  fi
  if poll_http_200 "http://127.0.0.1:${OPERATOR_PORT}/health" 15; then
    log "boot: operator UI /health HTTP 200 at :${OPERATOR_PORT}"
    return 0
  fi
  log "boot: operator UI not ready on :${OPERATOR_PORT}"
  return 1
}

parse_serial_usl() {
  local serial_log="$1"
  USL_SERIAL_OK=0
  USL_SERIAL_PHASE2_OK=0
  if grep -q '"event":"usl"' "$serial_log" 2>/dev/null && grep '"event":"usl"' "$serial_log" | grep -q '"status":"ok"'; then
    USL_SERIAL_OK=1
  fi
  if grep '"event":"usl"' "$serial_log" 2>/dev/null | grep -q '"phase":2' \
    && grep '"event":"usl"' "$serial_log" | grep -q '"broker":"ok"'; then
    USL_SERIAL_PHASE2_OK=1
  fi
}

parse_serial_hardware() {
  local serial_log="$1"
  HARDWARE_SERIAL_OK=0
  HARDWARE_READY=0
  if grep -q '"event":"hardware"' "$serial_log" 2>/dev/null \
    && grep '"event":"hardware"' "$serial_log" | grep -q '"status":"ready"'; then
    HARDWARE_SERIAL_OK=1
  fi
  if grep -q '/run/cog/hardware.ready' "$serial_log" 2>/dev/null; then
    HARDWARE_READY=1
  fi
}

run_megaton_live() {
  local phase="$1"
  local rounds="${USL_MEGATON_ROUNDS:-${COG_USL_MEGATON_ROUNDS:-3}}"
  export USL_STRESS_BASE="http://127.0.0.1:${USL_PORT}"
  export USL_STRESS_REQUIRE=1
  log "boot: Megaton phase ${phase} live (--require-live rounds=${rounds})"
  if python3 -m tools.stress.usl_megaton_chaos_hammer \
    --phase "$phase" \
    --rounds "$rounds" \
    --require-live \
    --usl-base "$USL_STRESS_BASE"; then
    MEGATON_PASS=1
    return 0
  fi
  MEGATON_PASS=0
  return 1
}

run_contract_boot() {
  ROOTFS_ARTIFACT="${ROOTFS:-${COG_ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-${PROFILE}}}"
  ROOTFS="$(resolve_cog_rootfs "$ROOTFS_ARTIFACT")"

  if [[ ! -d "$ROOTFS/usr" ]]; then
    log "FAIL: rootfs missing at $ROOTFS (run: make cog-rootfs COG_PROFILE=$PROFILE)"
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "fail" "[]" \
      '{"error":"rootfs_missing","rootfs":"'"$ROOTFS"'","artifact":"'"$ROOTFS_ARTIFACT"'"}'
    return 1
  fi

  if ! command -v qemu-system-x86_64 >/dev/null 2>&1; then
    log "SKIP: qemu-system-x86_64 not installed"
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "skip" "[]" '{"reason":"qemu_not_installed"}'
    return 0
  fi

  local disk_img
  disk_img="$(materialize_rootfs_disk)" || {
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "fail" "[]" '{"error":"disk_image_failed"}'
    return 1
  }

  local kernel="$ROOTFS/boot/vmlinuz"
  local initrd="$ROOTFS/boot/initrd.img"
  if [[ ! -f "$kernel" ]]; then
    kernel="$(find "$ROOTFS/boot" -maxdepth 1 -name 'vmlinuz*' -type f 2>/dev/null | head -1 || true)"
  fi
  if [[ ! -f "$initrd" ]]; then
    initrd="$(find "$ROOTFS/boot" -maxdepth 1 -name 'initrd*.img' -type f 2>/dev/null | head -1 || true)"
  fi

  local serial_log="$ARTIFACT_DIR/qemu-serial.log"
  : >"$serial_log"
  local pattern='"event":"contract"'

  local -a qemu_cmd=(
    qemu-system-x86_64 -nographic -m 1024
    -serial "file:$serial_log"
    -drive "file=$disk_img,format=raw,if=virtio"
    -netdev "user,id=net0,hostfwd=tcp:127.0.0.1:${AAIS_PORT}-:${AAIS_PORT},hostfwd=tcp:127.0.0.1:${USL_PORT}-:${USL_PORT},hostfwd=tcp:127.0.0.1:${OPERATOR_PORT}-:${OPERATOR_PORT}"
    -device "virtio-net-pci,netdev=net0"
  )
  if [[ -n "$kernel" && -f "$kernel" ]]; then
    qemu_cmd+=(-kernel "$kernel")
    [[ -n "$initrd" && -f "$initrd" ]] && qemu_cmd+=(-initrd "$initrd")
    qemu_cmd+=(-append "console=ttyS0 root=/dev/vda rw init=/sbin/init profile=$PROFILE")
  else
    log "WARN: kernel not found under $ROOTFS/boot; boot may fail"
    qemu_cmd+=(-append "console=ttyS0 root=/dev/vda rw init=/sbin/init profile=$PROFILE")
  fi

  log "boot: launching QEMU (timeout ${TIMEOUT_SEC}s) profile=$PROFILE disk=$disk_img"
  "${qemu_cmd[@]}" >>"$CONTRACT_LOG" 2>&1 &
  local qpid=$!
  local elapsed=0
  local found=0
  while [[ "$elapsed" -lt "$TIMEOUT_SEC" ]]; do
    if grep -q "$pattern" "$serial_log" 2>/dev/null; then
      found=1
      break
    fi
    if ! kill -0 "$qpid" 2>/dev/null; then
      break
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  local aais_ok=0 aais_http="000"
  local usl_ok=0 usl_broker_ok=0 usl_body=""
  local operator_ok=0 operator_http="000"
  local usl_serial_ok=0 usl_serial_phase2_ok=0
  local hardware_serial_ok=0 hardware_ready=0
  local megaton_pass=0 megaton_phase2=0 megaton_skipped=1

  if [[ "$found" -eq 1 ]]; then
    if poll_aais_health; then
      aais_ok=1
      aais_http="200"
    else
      aais_http="$(curl -sf -o /dev/null -w '%{http_code}' "http://127.0.0.1:${AAIS_PORT}/health" 2>/dev/null || echo "000")"
    fi

    local require_broker=0
    if [[ "$USL_SLICE2" -eq 1 ]] || [[ "$PROFILE" == "metal" ]]; then
      require_broker=1
    fi
    if usl_body="$(poll_usl_health "$require_broker")"; then
      usl_ok=1
      if [[ "$require_broker" -eq 1 ]] && python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d.get("phase")==2 and d.get("broker")=="ok" else 1)' "$usl_body" 2>/dev/null; then
        usl_broker_ok=1
      elif [[ "$require_broker" -eq 0 ]]; then
        usl_broker_ok=0
      fi
    fi

    if [[ "$PROFILE" == "daily-driver" ]]; then
      if poll_operator_ui; then
        operator_ok=1
        operator_http="200"
      else
        operator_http="$(curl -sf -o /dev/null -w '%{http_code}' "http://127.0.0.1:${OPERATOR_PORT}/app/" 2>/dev/null || echo "000")"
      fi
    fi

    parse_serial_usl "$serial_log"
    usl_serial_ok=$USL_SERIAL_OK
    usl_serial_phase2_ok=$USL_SERIAL_PHASE2_OK

    parse_serial_hardware "$serial_log"
    hardware_serial_ok=$HARDWARE_SERIAL_OK
    if [[ -f "$ROOTFS/run/cog/hardware.ready" ]]; then
      hardware_ready=1
    fi

    if [[ "$USL_SLICE2" -eq 1 ]]; then
      megaton_skipped=0
      if run_megaton_live 2; then
        megaton_phase2=1
        megaton_pass=1
      fi
    elif [[ "$USL_MEGATON" -eq 1 ]]; then
      megaton_skipped=0
      if run_megaton_live 1; then
        megaton_pass=1
      fi
    fi
  fi

  kill "$qpid" 2>/dev/null || true
  wait "$qpid" 2>/dev/null || true
  cat "$serial_log" >>"$CONTRACT_LOG" || true

  local events_seen aais_events usl_events hardware_events
  events_seen="$(grep -c 'event":"contract"' "$serial_log" 2>/dev/null | head -1 || echo 0)"
  aais_events="$(grep -c 'event":"aais"' "$serial_log" 2>/dev/null | head -1 || echo 0)"
  usl_events="$(grep -c 'event":"usl"' "$serial_log" 2>/dev/null | head -1 || echo 0)"
  hardware_events="$(grep -c 'event":"hardware"' "$serial_log" 2>/dev/null | head -1 || echo 0)"

  export COG_QEMU_EVENTS_SEEN="${events_seen:-0}"
  export COG_QEMU_AAIS_EVENTS="${aais_events:-0}"
  export COG_QEMU_USL_EVENTS="${usl_events:-0}"
  export COG_QEMU_HARDWARE_EVENTS="${hardware_events:-0}"
  export COG_QEMU_HARDWARE_SERIAL_OK="$hardware_serial_ok"
  export COG_QEMU_HARDWARE_READY="$hardware_ready"
  export COG_QEMU_AAIS_OK="$aais_ok"
  export COG_QEMU_AAIS_HTTP="$aais_http"
  export COG_QEMU_USL_OK="$usl_ok"
  export COG_QEMU_USL_BROKER_OK="$usl_broker_ok"
  export COG_QEMU_USL_SERIAL_OK="$usl_serial_ok"
  export COG_QEMU_USL_SERIAL_PHASE2_OK="$usl_serial_phase2_ok"
  export COG_QEMU_OPERATOR_OK="$operator_ok"
  export COG_QEMU_OPERATOR_HTTP="$operator_http"
  export COG_QEMU_MEGATON_SKIPPED="$megaton_skipped"
  export COG_QEMU_MEGATON_PASS="$megaton_pass"
  export COG_QEMU_MEGATON_PHASE2="$megaton_phase2"
  export COG_QEMU_MEGATON_REPORT="$MEGATON_REPORT"
  export COG_QEMU_ELAPSED="$elapsed"
  export COG_QEMU_SERIAL_LOG="$serial_log"
  export COG_QEMU_DISK_IMAGE="$disk_img"
  export COG_QEMU_ROOTFS="$ROOTFS"
  export COG_QEMU_ROOTFS_ARTIFACT="$ROOTFS_ARTIFACT"

  local extra
  extra="$(python3 - <<'PY'
import json, os

def _int(name: str) -> int:
    raw = (os.environ.get(name) or "0").strip().split()
    if not raw:
        return 0
    try:
        return int(raw[0])
    except ValueError:
        return 0

def _bool(name: str) -> bool:
    return _int(name) != 0

extra = {
    "events_seen": _int("COG_QEMU_EVENTS_SEEN"),
    "aais_events_seen": _int("COG_QEMU_AAIS_EVENTS"),
    "usl_events_seen": _int("COG_QEMU_USL_EVENTS"),
    "hardware_events_seen": _int("COG_QEMU_HARDWARE_EVENTS"),
    "hardware_serial_ready": _bool("COG_QEMU_HARDWARE_SERIAL_OK"),
    "hardware_ready": _bool("COG_QEMU_HARDWARE_READY"),
    "aais_health_200": _bool("COG_QEMU_AAIS_OK"),
    "aais_http_code": os.environ.get("COG_QEMU_AAIS_HTTP", "000"),
    "usl_health_200": _bool("COG_QEMU_USL_OK"),
    "usl_broker_ok": _bool("COG_QEMU_USL_BROKER_OK"),
    "usl_serial_ok": _bool("COG_QEMU_USL_SERIAL_OK"),
    "usl_serial_phase2_ok": _bool("COG_QEMU_USL_SERIAL_PHASE2_OK"),
    "operator_ui_http_200": _bool("COG_QEMU_OPERATOR_OK"),
    "operator_http_code": os.environ.get("COG_QEMU_OPERATOR_HTTP", "000"),
    "usl_megaton_skipped": _bool("COG_QEMU_MEGATON_SKIPPED"),
    "usl_megaton_pass": _bool("COG_QEMU_MEGATON_PASS"),
    "usl_megaton_phase2": _bool("COG_QEMU_MEGATON_PHASE2"),
    "megaton_report": os.environ.get("COG_QEMU_MEGATON_REPORT", ""),
    "elapsed_sec": _int("COG_QEMU_ELAPSED"),
    "serial_log": os.environ.get("COG_QEMU_SERIAL_LOG", ""),
    "disk_image": os.environ.get("COG_QEMU_DISK_IMAGE", ""),
    "rootfs": os.environ.get("COG_QEMU_ROOTFS", ""),
    "rootfs_artifact": os.environ.get("COG_QEMU_ROOTFS_ARTIFACT", ""),
}
print(json.dumps(extra))
PY
)"

  local -a checks=("serial contract ready")
  [[ "$aais_ok" -eq 1 ]] && checks+=("aais_health_200")
  [[ "$usl_ok" -eq 1 ]] && checks+=("usl_health_200")
  [[ "$usl_broker_ok" -eq 1 ]] && checks+=("usl_broker_ok")
  [[ "$usl_serial_ok" -eq 1 ]] && checks+=("usl_serial_ok")
  [[ "$usl_serial_phase2_ok" -eq 1 ]] && checks+=("usl_serial_phase2_ok")
  [[ "$hardware_serial_ok" -eq 1 ]] && checks+=("hardware_serial_ready")
  [[ "$operator_ok" -eq 1 ]] && checks+=("operator_ui_http_200")
  [[ "$megaton_pass" -eq 1 ]] && checks+=("usl_megaton_pass")

  local checks_json
  checks_json="$(printf '%s\n' "${checks[@]}" | python3 -c 'import json,sys; print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')"

  local pass=0
  if [[ "$found" -eq 1 && "$aais_ok" -eq 1 ]]; then
    pass=1
    if [[ "$PROFILE" == "daily-driver" ]]; then
      [[ "$usl_ok" -eq 1 && "$operator_ok" -eq 1 && "$hardware_serial_ok" -eq 1 ]] || pass=0
    fi
    if [[ "$USL_SLICE2" -eq 1 ]]; then
      [[ "$usl_ok" -eq 1 && "$usl_broker_ok" -eq 1 && "$usl_serial_phase2_ok" -eq 1 && "$megaton_pass" -eq 1 ]] || pass=0
    elif [[ "$USL_MEGATON" -eq 1 ]]; then
      [[ "$usl_ok" -eq 1 && "$usl_serial_ok" -eq 1 && "$megaton_pass" -eq 1 ]] || pass=0
    fi
  fi

  if [[ "$pass" -eq 1 ]]; then
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "pass" "$checks_json" "$extra"
    cp -f "$CONTRACT_JSON_BOOT" "$CONTRACT_JSON"
    log "boot contract: pass -> $CONTRACT_JSON_BOOT"
    return 0
  fi

  write_contract_json "$CONTRACT_JSON_BOOT" "boot" "fail" "$checks_json" "$extra"
  cp -f "$CONTRACT_JSON_BOOT" "$CONTRACT_JSON"
  if [[ "$found" -ne 1 ]]; then
    log "boot contract: fail (no contract JSON on serial within ${TIMEOUT_SEC}s)"
  else
    log "boot contract: fail (health/operator/megaton gates)"
  fi
  return 1
}

if [[ "$CONTRACT" -eq 1 ]]; then
  run_static_contract || exit 1
  if [[ "$CONTRACT_BOOT" -eq 1 ]]; then
    run_contract_boot || exit 1
  fi
  exit 0
fi

if [[ "$BUILD" -eq 1 ]]; then
  bash "$COG_OS_DIR/forge/scripts/build-rootfs.sh" --profile "$PROFILE"
  ROOTFS="$REPO_ROOT/artifacts/cog-os/rootfs-${PROFILE}"
fi

ROOTFS="${ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-${PROFILE}}"
log "qemu-smoke: profile=$PROFILE rootfs=$ROOTFS (interactive boot not implemented in default mode)"
exit 0
