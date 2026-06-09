#!/usr/bin/env bash
# QEMU smoke / contract checks for Nova NorthStar CoG OS (cog-os/).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COG_OS_DIR="$REPO_ROOT/cog-os"
HOST_DIR="$COG_OS_DIR/host"
# shellcheck source=../../forge/scripts/lib/resolve-rootfs.sh
source <(sed 's/\r$//' "$COG_OS_DIR/forge/scripts/lib/resolve-rootfs.sh")

PROFILE="${COG_PROFILE:-metal}"
CONTRACT=0
CONTRACT_BOOT=0
BUILD=0
ROOTFS=""
TIMEOUT_SEC="${COG_QEMU_TIMEOUT:-180}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}"
GATEKEEPER_MARK="Nova NorthStar CoG OS gatekeeper PID1 starting"
AAIS_PORT="${COG_AAIS_PORT:-8765}"
OPERATOR_PORT="${COG_OPERATOR_PORT:-8000}"

usage() {
  echo "usage: qemu-smoke.sh [--profile metal|daily-driver] [--build] [--rootfs PATH]" >&2
  echo "       qemu-smoke.sh --contract [--contract-boot] [--profile NAME]" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --build) BUILD=1; shift ;;
    --rootfs) ROOTFS="$2"; shift 2 ;;
    --contract) CONTRACT=1; shift ;;
    --contract-boot) CONTRACT=1; CONTRACT_BOOT=1; shift ;;
    -h|--help) usage ;;
    *) echo "unknown: $1" >&2; usage ;;
  esac
done

mkdir -p "$ARTIFACT_DIR"
CONTRACT_JSON_STATIC="$ARTIFACT_DIR/qemu-contract-static.json"
CONTRACT_JSON_BOOT="$ARTIFACT_DIR/qemu-contract-boot.json"
CONTRACT_JSON="$ARTIFACT_DIR/qemu-contract.json"
CONTRACT_LOG="$ARTIFACT_DIR/qemu-contract.log"
: >"$CONTRACT_LOG"

log() { echo "$@" | tee -a "$CONTRACT_LOG" >&2; }

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
  check "aais.sh bash -n" bash -n "$HOST_DIR/rootfs/etc/cog/services/aais.sh"
  check "profile metal.yaml" test -f "$COG_OS_DIR/forge/profiles/metal.yaml"
  check "profile daily-driver.yaml" test -f "$COG_OS_DIR/forge/profiles/daily-driver.yaml"
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
  local size_mb="${COG_ROOTFS_IMG_MB:-2048}"

  if [[ -f "$img" ]]; then
    local rootfs_stamp="$ROOTFS/.cog-build-stamp"
    if [[ -f "$rootfs_stamp" && "$rootfs_stamp" -nt "$img" ]]; then
      log "boot: reuse disk image $img"
      echo "$img"
      return 0
    fi
  fi

  log "boot: building ext4 disk image ($size_mb MB) from $ROOTFS"
  rm -f "$img"
  qemu-img create -f raw "$img" "${size_mb}M" >>"$CONTRACT_LOG" 2>&1

  if mkfs.ext4 -F -d "$ROOTFS" "$img" >>"$CONTRACT_LOG" 2>&1; then
    log "boot: mkfs.ext4 -d populated $img"
    echo "$img"
    return 0
  fi

  log "boot: mkfs.ext4 -d unavailable; falling back to loop mount"
  local mount_di
  mount_dir="$(mktemp -d "${TMPDIR:-/tmp}/cog-rootfs-mnt.XXXXXX")"
  mkfs.ext4 -F "$img" >>"$CONTRACT_LOG" 2>&1
  local loop_dev=""
  if command -v losetup >/dev/null 2>&1; then
    loop_dev="$(losetup --find --show "$img")"
    mount "$loop_dev" "$mount_dir"
    rsync -a "$ROOTFS/" "$mount_dir/"
    sync
    umount "$mount_dir"
    losetup -d "$loop_dev"
  else
    log "FAIL: cannot populate disk (need mkfs.ext4 -d or losetup+mount)"
    rmdir "$mount_dir" 2>/dev/null || true
    return 1
  fi
  rmdir "$mount_dir" 2>/dev/null || true
  echo "$img"
}

poll_aais_health() {
  local elapsed=0
  local limit="${COG_AAIS_POLL_SEC:-30}"
  local code="000"
  while [[ "$elapsed" -lt "$limit" ]]; do
    code="$(curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 "http://127.0.0.1:${AAIS_PORT}/health" 2>/dev/null || true)"
    code="${code:-000}"
    if [[ "$code" == "200" ]]; then
      log "boot: AAIS /health HTTP 200"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  log "boot: AAIS /health not ready (last HTTP $code)"
  return 1
}

poll_operator_ui() {
  local elapsed=0
  local limit="${COG_OPERATOR_POLL_SEC:-45}"
  local code="000"
  while [[ "$elapsed" -lt "$limit" ]]; do
    code="$(curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 "http://127.0.0.1:${OPERATOR_PORT}/app/" 2>/dev/null || true)"
    code="${code:-000}"
    if [[ "$code" == "200" ]]; then
      log "boot: operator UI /app/ HTTP 200"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  log "boot: operator UI /app/ not ready (last HTTP $code)"
  return 1
}

run_contract_boot() {
  local artifact_rootfs="${ROOTFS:-$REPO_ROOT/artifacts/cog-os/rootfs-${PROFILE}}"
  ROOTFS="$(resolve_cog_rootfs "$artifact_rootfs")"
  if [[ ! -d "$ROOTFS/usr" ]]; then
    log "FAIL: rootfs missing at $ROOTFS (artifact=$artifact_rootfs; run: make cog-rootfs COG_PROFILE=$PROFILE)"
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "fail" "[]" '{"error":"rootfs_missing","rootfs":"'"$ROOTFS"'","artifact":"'"$artifact_rootfs"'"}'
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
    kernel="$(find "$ROOTFS" -name 'vmlinuz*' -type f 2>/dev/null | head -1 || true)"
  fi
  if [[ ! -f "$initrd" ]]; then
    initrd="$(find "$ROOTFS" -name 'initrd*' -type f 2>/dev/null | head -1 || true)"
  fi

  local serial_log="$ARTIFACT_DIR/qemu-serial.log"
  : >"$serial_log"
  local pattern='"event":"contract"'

  local -a qemu_cmd=(
    qemu-system-x86_64 -nographic -m 512
    -serial "file:$serial_log"
    -drive "file=$disk_img,format=raw,if=virtio"
    -netdev "user,id=net0,hostfwd=tcp::${AAIS_PORT}-:${AAIS_PORT}"
    -device "virtio-net-pci,netdev=net0"
  )
  if [[ "$PROFILE" == "daily-driver" ]]; then
    qemu_cmd=(
      qemu-system-x86_64 -nographic -m 1024
      -serial "file:$serial_log"
      -drive "file=$disk_img,format=raw,if=virtio"
      -netdev "user,id=net0,hostfwd=tcp::${AAIS_PORT}-:${AAIS_PORT},hostfwd=tcp::${OPERATOR_PORT}-:${OPERATOR_PORT}"
      -device "virtio-net-pci,netdev=net0"
    )
  fi
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

  local aais_ok=0
  local aais_http="000"
  local operator_ok=0
  local operator_http="000"
  if [[ "$found" -eq 1 ]]; then
    sleep 2
    if poll_aais_health; then
      aais_ok=1
      aais_http="200"
    else
      aais_http="$(curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 "http://127.0.0.1:${AAIS_PORT}/health" 2>/dev/null || true)"
      aais_http="${aais_http:-000}"
    fi
    if [[ "$PROFILE" == "daily-driver" ]]; then
      if poll_operator_ui; then
        operator_ok=1
        operator_http="200"
      else
        operator_http="$(curl -sf -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 3 "http://127.0.0.1:${OPERATOR_PORT}/app/" 2>/dev/null || true)"
        operator_http="${operator_http:-000}"
      fi
    else
      operator_ok=1
    fi
  fi

  kill "$qpid" 2>/dev/null || true
  wait "$qpid" 2>/dev/null || true
  cat "$serial_log" >>"$CONTRACT_LOG" || true

  local events_seen aais_events
  events_seen="$(grep -c 'event":"contract"' "$serial_log" 2>/dev/null || true)"
  events_seen="${events_seen:-0}"
  aais_events="$(grep -c 'event":"aais"' "$serial_log" 2>/dev/null || true)"
  aais_events="${aais_events:-0}"
  local extra
  extra="$(python3 - <<PY
import json
print(json.dumps({
    "events_seen": int("$events_seen"),
    "aais_events_seen": int("$aais_events"),
    "aais_health_200": ${aais_ok},
    "aais_http_code": "$aais_http",
    "operator_ui_http_200": ${operator_ok},
    "operator_http_code": "$operator_http",
    "operator_port": int("${OPERATOR_PORT}"),
    "elapsed_sec": int("$elapsed"),
    "serial_log": "$serial_log",
    "disk_image": "$disk_img",
}))
PY
)"

  local checks_json='["serial contract ready"]'
  if [[ "$aais_ok" -eq 1 ]]; then
    checks_json='["serial contract ready","aais_health_200"]'
  fi
  if [[ "$PROFILE" == "daily-driver" && "$operator_ok" -eq 1 ]]; then
    checks_json='["serial contract ready","aais_health_200","operator_ui_http_200"]'
  elif [[ "$PROFILE" != "daily-driver" && "$aais_ok" -eq 1 ]]; then
    checks_json='["serial contract ready","aais_health_200"]'
  fi

  local boot_pass=0
  if [[ "$found" -eq 1 && "$aais_ok" -eq 1 ]]; then
    if [[ "$PROFILE" == "daily-driver" ]]; then
      [[ "$operator_ok" -eq 1 ]] && boot_pass=1
    else
      boot_pass=1
    fi
  fi

  if [[ "$boot_pass" -eq 1 ]]; then
    write_contract_json "$CONTRACT_JSON_BOOT" "boot" "pass" "$checks_json" "$extra"
    cp -f "$CONTRACT_JSON_BOOT" "$CONTRACT_JSON"
    log "boot contract: pass -> $CONTRACT_JSON_BOOT"
    return 0
  fi

  write_contract_json "$CONTRACT_JSON_BOOT" "boot" "fail" "$checks_json" "$extra"
  cp -f "$CONTRACT_JSON_BOOT" "$CONTRACT_JSON"
  if [[ "$found" -ne 1 ]]; then
    log "boot contract: fail (no contract JSON on serial within ${TIMEOUT_SEC}s)"
  elif [[ "$aais_ok" -ne 1 ]]; then
    log "boot contract: fail (AAIS /health not HTTP 200)"
  elif [[ "$PROFILE" == "daily-driver" && "$operator_ok" -ne 1 ]]; then
    log "boot contract: fail (operator UI /app/ not HTTP 200)"
  else
    log "boot contract: fail"
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
ROOTFS="$(resolve_cog_rootfs "$ROOTFS")"
log "qemu-smoke: profile=$PROFILE rootfs=$ROOTFS (interactive boot not implemented in default mode)"
exit 0
