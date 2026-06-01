#!/usr/bin/env bash
set -euo pipefail

COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../paths.sh
source "$COMMON_DIR/../../paths.sh"

INSTALLER_STATE_DIR="${INSTALLER_STATE_DIR:-/tmp/cogos-installer}"
INSTALLER_CHECKPOINT_DIR=""
INSTALLER_EVENTS_LOG=""
INSTALLER_PLAN_FILE=""
INSTALLER_CURRENT_STEP_FILE=""
INSTALLER_LOG_FILE=""
INSTALLER_STATE_JSON=""

log() {
  printf '[cogos-installer] %s\n' "$*"
}

warn() {
  printf '[cogos-installer][warn] %s\n' "$*" >&2
}

die() {
  printf '[cogos-installer][error] %s\n' "$*" >&2
  exit 1
}

require_tools() {
  local t
  for t in "$@"; do
    command -v "$t" >/dev/null 2>&1 || die "Missing required tool: $t"
  done
}

require_root() {
  [[ "${EUID:-$(id -u)}" -eq 0 ]] || die "Installer apply mode requires root."
}

is_nvme_device() {
  local disk="$1"
  [[ "$disk" == /dev/nvme* ]]
}

part_suffix() {
  local disk="$1"
  case "$disk" in
    /dev/nvme*|/dev/mmcblk*|/dev/loop*) printf 'p' ;;
    *) printf '' ;;
  esac
}

run_cmd() {
  if [[ "${INSTALLER_APPLY:-0}" == "1" ]]; then
    "$@"
  else
    printf 'PLAN: '
    printf '%q ' "$@"
    printf '\n'
  fi
}

emit_plan_line() {
  local line="$1"
  printf '%s\n' "$line" >>"$INSTALLER_PLAN_FILE"
}

reset_plan() {
  : >"$INSTALLER_PLAN_FILE"
}

timestamp_utc() {
  date -u +%Y-%m-%dT%H:%M:%SZ
}

init_installer_state() {
  local resume="${1:-0}"
  mkdir -p "$INSTALLER_STATE_DIR"
  INSTALLER_CHECKPOINT_DIR="$INSTALLER_STATE_DIR/checkpoints"
  INSTALLER_EVENTS_LOG="$INSTALLER_STATE_DIR/events.log"
  INSTALLER_PLAN_FILE="$INSTALLER_STATE_DIR/plan.txt"
  INSTALLER_CURRENT_STEP_FILE="$INSTALLER_STATE_DIR/current_step"
  INSTALLER_STATE_JSON="$INSTALLER_STATE_DIR/state.json"

  mkdir -p "$INSTALLER_CHECKPOINT_DIR"
  touch "$INSTALLER_EVENTS_LOG" "$INSTALLER_PLAN_FILE" "$INSTALLER_STATE_JSON"

  if [[ "$resume" != "1" ]]; then
    rm -f "$INSTALLER_CHECKPOINT_DIR"/*.status 2>/dev/null || true
    rm -f "$INSTALLER_CURRENT_STEP_FILE" 2>/dev/null || true
    : >"$INSTALLER_EVENTS_LOG"
    : >"$INSTALLER_PLAN_FILE"
    : >"$INSTALLER_STATE_JSON"
    rm -f "$INSTALLER_STATE_DIR"/state-* 2>/dev/null || true
  fi

  if [[ -z "$(get_state_value run_id || true)" ]]; then
    set_state_value run_id "$(date -u +%Y%m%dT%H%M%SZ)-$$"
  fi
  if [[ -z "$(get_state_value run_started_at || true)" ]]; then
    set_state_value run_started_at "$(timestamp_utc)"
  fi
  set_state_value state_dir "$INSTALLER_STATE_DIR"
  refresh_state_json
}

start_install_log_capture() {
  local mode="${1:-plan}"
  local ts
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  INSTALLER_LOG_FILE="${INSTALLER_LOG_FILE:-$INSTALLER_STATE_DIR/install-${mode}-${ts}.log}"
  touch "$INSTALLER_LOG_FILE"
  exec > >(tee -a "$INSTALLER_LOG_FILE") 2>&1
}

checkpoint_file_for() {
  local step="$1"
  printf '%s/%s.status' "$INSTALLER_CHECKPOINT_DIR" "$step"
}

checkpoint_field() {
  local step="$1"
  local key="$2"
  local f
  f="$(checkpoint_file_for "$step")"
  if [[ -f "$f" ]]; then
    awk -F= -v k="$key" '$1==k{print substr($0, index($0, "=")+1); exit}' "$f"
  fi
}

checkpoint_status() {
  local step="$1"
  local status
  status="$(checkpoint_field "$step" "status" || true)"
  if [[ -n "$status" ]]; then
    printf '%s' "$status"
    return
  fi
  printf 'pending'
}

is_step_completed() {
  local step="$1"
  [[ "$(checkpoint_status "$step")" == "completed" ]]
}

append_event() {
  local kind="$1"
  local step="$2"
  local message="${3:-}"
  printf '%s kind=%s step=%s message=%q\n' "$(timestamp_utc)" "$kind" "$step" "$message" >>"$INSTALLER_EVENTS_LOG"
}

set_current_step() {
  local step="$1"
  printf '%s\n' "$step" >"$INSTALLER_CURRENT_STEP_FILE"
}

clear_current_step() {
  rm -f "$INSTALLER_CURRENT_STEP_FILE" 2>/dev/null || true
}

mark_checkpoint() {
  local step="$1"
  local status="$2"
  local message="${3:-}"
  local f tmp now started_at finished_at error
  now="$(timestamp_utc)"
  started_at="$(checkpoint_field "$step" "started_at" || true)"
  finished_at="$(checkpoint_field "$step" "finished_at" || true)"
  error=""

  if [[ -z "$started_at" ]]; then
    started_at="$now"
  fi
  if [[ "$status" == "in_progress" ]]; then
    finished_at=""
  elif [[ "$status" == "completed" || "$status" == "failed" ]]; then
    finished_at="$now"
  fi
  if [[ "$status" == "failed" ]]; then
    error="$message"
  fi

  f="$(checkpoint_file_for "$step")"
  tmp="${f}.tmp"
  {
    printf 'step=%s\n' "$step"
    printf 'status=%s\n' "$status"
    printf 'timestamp=%s\n' "$now"
    printf 'started_at=%s\n' "$started_at"
    printf 'finished_at=%s\n' "$finished_at"
    printf 'error=%s\n' "$error"
    printf 'message=%s\n' "$message"
  } >"$tmp"
  mv -f "$tmp" "$f"
  append_event "checkpoint" "$step" "$status ${message:+- $message}"
  refresh_state_json
}

step_start() {
  local step="$1"
  set_current_step "$step"
  mark_checkpoint "$step" "in_progress" "started"
}

step_complete() {
  local step="$1"
  mark_checkpoint "$step" "completed" "ok"
}

step_fail() {
  local step="$1"
  local message="${2:-failed}"
  mark_checkpoint "$step" "failed" "$message"
}

state_value_file() {
  local key="$1"
  printf '%s/state-%s' "$INSTALLER_STATE_DIR" "$key"
}

set_state_value() {
  local key="$1"
  local value="$2"
  local f tmp
  f="$(state_value_file "$key")"
  tmp="${f}.tmp"
  printf '%s\n' "$value" >"$tmp"
  mv -f "$tmp" "$f"
}

get_state_value() {
  local key="$1"
  local f
  f="$(state_value_file "$key")"
  [[ -f "$f" ]] && cat "$f"
}

refresh_state_json() {
  local step_order run_id run_started_at run_mode target_disk rootfs_source install_hostname install_user installer_version cogos_tag system_hostname now
  step_order="$(get_state_value step_order || true)"
  run_id="$(get_state_value run_id || true)"
  run_started_at="$(get_state_value run_started_at || true)"
  run_mode="$(get_state_value run_mode || true)"
  target_disk="$(get_state_value target_disk || true)"
  rootfs_source="$(get_state_value rootfs_source || true)"
  install_hostname="$(get_state_value install_hostname || true)"
  install_user="$(get_state_value install_user || true)"
  installer_version="$(get_state_value installer_version || true)"
  cogos_tag="$(get_state_value cogos_tag || true)"
  system_hostname="$(hostname 2>/dev/null || echo unknown)"
  now="$(timestamp_utc)"

  env \
    INSTALLER_CHECKPOINT_DIR="$INSTALLER_CHECKPOINT_DIR" \
    INSTALLER_STATE_JSON="$INSTALLER_STATE_JSON" \
    STATE_STEP_ORDER="$step_order" \
    STATE_RUN_ID="$run_id" \
    STATE_RUN_STARTED_AT="$run_started_at" \
    STATE_RUN_MODE="$run_mode" \
    STATE_TARGET_DISK="$target_disk" \
    STATE_ROOTFS_SOURCE="$rootfs_source" \
    STATE_INSTALL_HOSTNAME="$install_hostname" \
    STATE_INSTALL_USER="$install_user" \
    STATE_INSTALLER_VERSION="$installer_version" \
    STATE_COGOS_TAG="$cogos_tag" \
    STATE_SYSTEM_HOSTNAME="$system_hostname" \
    STATE_UPDATED_AT="$now" \
    STATE_DIR="$INSTALLER_STATE_DIR" \
    STATE_LOG_FILE="${INSTALLER_LOG_FILE:-}" \
    STATE_EVENTS_LOG="$INSTALLER_EVENTS_LOG" \
    python3 - <<'PY'
import json
import os
from pathlib import Path

checkpoint_dir = Path(os.environ["INSTALLER_CHECKPOINT_DIR"])
out_path = Path(os.environ["INSTALLER_STATE_JSON"])
tmp_path = out_path.with_suffix(".json.tmp")

step_order_raw = os.environ.get("STATE_STEP_ORDER", "")
ordered_steps = [s.strip() for s in step_order_raw.split(",") if s.strip()]

def parse_status(path: Path):
  data = {}
  for line in path.read_text(encoding="utf-8").splitlines():
    if "=" not in line:
      continue
    k, v = line.split("=", 1)
    data[k.strip()] = v.strip()
  return data

records = {}
for status_file in sorted(checkpoint_dir.glob("*.status")):
  payload = parse_status(status_file)
  step = payload.get("step", status_file.stem)
  records[step] = {
    "name": step,
    "status": payload.get("status", "pending"),
    "started_at": payload.get("started_at") or None,
    "finished_at": payload.get("finished_at") or None,
    "error": payload.get("error") or None,
  }

steps = []
for step in ordered_steps:
  steps.append(records.pop(step, {
    "name": step,
    "status": "pending",
    "started_at": None,
    "finished_at": None,
    "error": None,
  }))
for step_name in sorted(records.keys()):
  steps.append(records[step_name])

state = {
  "run": {
    "run_id": os.environ.get("STATE_RUN_ID") or None,
    "mode": os.environ.get("STATE_RUN_MODE") or None,
    "started_at": os.environ.get("STATE_RUN_STARTED_AT") or None,
    "updated_at": os.environ.get("STATE_UPDATED_AT") or None,
    "state_dir": os.environ.get("STATE_DIR") or None,
    "log_file": os.environ.get("STATE_LOG_FILE") or None,
    "events_log": os.environ.get("STATE_EVENTS_LOG") or None,
    "system_hostname": os.environ.get("STATE_SYSTEM_HOSTNAME") or None,
    "install_hostname": os.environ.get("STATE_INSTALL_HOSTNAME") or None,
    "install_user": os.environ.get("STATE_INSTALL_USER") or None,
    "target_disk": os.environ.get("STATE_TARGET_DISK") or None,
    "rootfs_source": os.environ.get("STATE_ROOTFS_SOURCE") or None,
    "cogos_tag": os.environ.get("STATE_COGOS_TAG") or None,
    "installer_version": os.environ.get("STATE_INSTALLER_VERSION") or None,
  },
  "steps": steps,
}

tmp_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
tmp_path.replace(out_path)
PY
}

safe_remove() {
  local path="$1"
  if [[ -e "$path" || -L "$path" ]]; then
    run_cmd rm -rf "$path"
  fi
}

write_install_proof() {
  local target_root="$1"
  local proof_path="$target_root/opt/cogos/memory/logs/install_proof.json"
  local state_proof_path="$INSTALLER_STATE_DIR/install_proof.json"
  local tmp_payload
  tmp_payload="$(mktemp)"
  cat >"$tmp_payload" <<EOF
{
  "installer": "cogos-installer",
  "mode": "$( [[ "${INSTALLER_APPLY:-0}" == "1" ]] && echo apply || echo plan )",
  "timestamp_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "target_disk": "${TARGET_DISK:-unknown}",
  "target_root": "$target_root",
  "rootfs_source": "${ROOTFS_SOURCE:-unknown}"
}
EOF
  log "Writing install proof to $proof_path (resume=${INSTALLER_RESUME:-0})"
  mkdir -p "$(dirname "$proof_path")"
  cat "$tmp_payload" >"$proof_path"
  log "Writing install proof to $state_proof_path (resume=${INSTALLER_RESUME:-0})"
  mkdir -p "$(dirname "$state_proof_path")"
  cat "$tmp_payload" >"$state_proof_path"
  rm -f "$tmp_payload"
}
