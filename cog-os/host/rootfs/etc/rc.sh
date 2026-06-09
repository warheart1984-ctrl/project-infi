#!/bin/bash
# Nova NorthStar CoG OS — service runner invoked by PID 1 gatekeeper.
set -euo pipefail

LOG=/var/log/cog/init.log
RUN=/run/cog
mkdir -p "$(dirname "$LOG")" "$RUN"

PROFILE="${COG_PROFILE:-}"
if [[ -z "$PROFILE" && -f /etc/cog/profile ]]; then
  PROFILE="$(tr -d '[:space:]' < /etc/cog/profile)"
fi
PROFILE="${PROFILE:-metal}"

INIT_MODE="${COG_INIT_MODE:-custom}"
if [[ -f /etc/cog/init_mode ]]; then
  INIT_MODE="$(tr -d '[:space:]' < /etc/cog/init_mode)"
fi

{
  echo "[rc.sh] Nova NorthStar CoG OS rc starting profile=${PROFILE} init_mode=${INIT_MODE}"
} >>"$LOG"

emit_serial_json() {
  local line="$1"
  echo "$line" >>"$LOG"
  printf '%s' "$line" > /dev/console 2>/dev/null || true
  printf '%s' "$line" > /dev/ttyS0 2>/dev/null || true
}

emit_contract_ready() {
  local line
  line="$(printf '{"event":"contract","status":"ready","profile":"%s","init_mode":"%s"}\n' "$PROFILE" "$INIT_MODE")"
  emit_serial_json "$line"
}

emit_aais_ready() {
  local line
  line='{"event":"aais","status":"ok"}'
  emit_serial_json "${line}"$'\n'
}

wait_for_aais_health() {
  local port="${COG_AAIS_PORT:-8765}"
  local attempt
  for attempt in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
      emit_aais_ready
      return 0
    fi
    sleep 1
  done
  echo "[rc.sh] AAIS health timeout on :${port}" >>"$LOG"
  return 1
}

should_run_service() {
  local name="$1"
  case "$name" in
    desktop)
      [[ "$INIT_MODE" == "hybrid" || "$PROFILE" == "daily-driver" ]]
      ;;
    login)
      [[ "$PROFILE" == "metal" ]]
      ;;
    *)
      return 0
      ;;
  esac
}

run_oneshot() {
  local script="$1"
  if [[ ! -x "$script" ]]; then
    echo "[rc.sh] skip missing oneshot $script" >>"$LOG"
    return 0
  fi
  echo "[rc.sh] oneshot $script" >>"$LOG"
  COG_PROFILE="$PROFILE" COG_INIT_MODE="$INIT_MODE" bash "$script" >>"$LOG" 2>&1 || {
    echo "[rc.sh] oneshot failed: $script" >>"$LOG"
    return 1
  }
}

run_daemon() {
  local script="$1"
  if [[ ! -x "$script" ]]; then
    echo "[rc.sh] skip missing daemon $script" >>"$LOG"
    return 0
  fi
  echo "[rc.sh] daemon $script" >>"$LOG"
  COG_PROFILE="$PROFILE" COG_INIT_MODE="$INIT_MODE" bash "$script" >>"$LOG" 2>&1 &
}

AAIS_ENABLED=0

while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs)"
  [[ -z "$line" ]] && continue

  read -r name kind path <<<"$line"
  name="${name:-$line}"
  kind="${kind:-oneshot}"
  path="${path:-/etc/cog/services/${name}.sh}"

  if ! should_run_service "$name"; then
    echo "[rc.sh] skip $name (profile=$PROFILE init_mode=$INIT_MODE)" >>"$LOG"
    continue
  fi

  if [[ "$name" == "aais" ]]; then
    AAIS_ENABLED=1
  fi

  case "$kind" in
    daemon) run_daemon "$path" ;;
    *) run_oneshot "$path" ;;
  esac
done < /etc/init.conf

if [[ "$AAIS_ENABLED" == "1" ]]; then
  wait_for_aais_health || true
fi

emit_contract_ready
echo "[rc.sh] ready profile=${PROFILE} init_mode=${INIT_MODE}" >>"$LOG"
touch "$RUN/rc.ready"

# PID 1 must not exit — reap and sleep.
while true; do
  wait -n 2>/dev/null || sleep 5
done
