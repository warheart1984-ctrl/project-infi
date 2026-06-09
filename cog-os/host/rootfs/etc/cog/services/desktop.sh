#!/bin/bash
# Daily-driver desktop stanza — gated on AAIS health (hybrid init; PID 1 stays custom).
set -euo pipefail

[[ "${COG_PROFILE:-}" == "daily-driver" ]] || exit 0

HEALTH_URL="${COG_AAIS_HEALTH_URL:-http://127.0.0.1:8765/health}"
OPERATOR_URL="${COG_OPERATOR_URL:-http://127.0.0.1:8000/app/}"
LOG=/var/log/cog/init.log

echo "[desktop] waiting for AAIS health at $HEALTH_URL" >>"$LOG"
ready=0
for _ in $(seq 1 45); do
  if command -v curl >/dev/null 2>&1 && curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if [[ -f /run/cog/aais.health ]]; then
    ready=1
    break
  fi
  sleep 2
done

if [[ "$ready" != "1" ]]; then
  echo "[desktop] AAIS health not ready; skipping desktop" >>"$LOG"
  exit 1
fi

echo "[desktop] waiting for operator UI at $OPERATOR_URL" >>"$LOG"
ui_ready=0
for _ in $(seq 1 30); do
  if command -v curl >/dev/null 2>&1 && curl -sf -o /dev/null "$OPERATOR_URL"; then
    ui_ready=1
    break
  fi
  if [[ -f /run/cog/operator_ui.health ]]; then
    ui_ready=1
    break
  fi
  sleep 2
done

if [[ "$ui_ready" != "1" ]]; then
  echo "[desktop] operator UI not ready; skipping desktop" >>"$LOG"
  exit 1
fi

echo "[desktop] AAIS + operator UI healthy; starting session stack" >>"$LOG"

if command -v dbus-daemon >/dev/null 2>&1; then
  mkdir -p /var/run/dbus
  if [[ ! -S /var/run/dbus/system_bus_socket ]]; then
    dbus-daemon --system --fork >>"$LOG" 2>&1 || true
  fi
fi

COGOS_UID="$(id -u cogos 2>/dev/null || echo 1000)"
COGOS_RUNTIME="/run/user/${COGOS_UID}"

if id cogos >/dev/null 2>&1 && command -v systemd >/dev/null 2>&1; then
  mkdir -p "$COGOS_RUNTIME"
  chown cogos:cogos "$COGOS_RUNTIME" 2>/dev/null || true
  runuser -u cogos -- systemd --user --collect >>"$LOG" 2>&1 &
fi

if [[ -x /usr/sbin/lightdm ]]; then
  /usr/sbin/lightdm >>"$LOG" 2>&1 &
fi

touch /run/cog/desktop.started
echo "[desktop] started" >>"$LOG"
