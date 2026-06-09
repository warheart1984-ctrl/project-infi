#!/bin/bash
# Metal profile console login — autologin cogos on primary TTY and serial.
set -euo pipefail

[[ "${COG_PROFILE:-metal}" == "metal" ]] || exit 0

LOG=/var/log/cog/init.log
USER="${COGOS_USER:-cogos}"

if ! id "$USER" >/dev/null 2>&1; then
  echo "[login] user $USER missing; skipping getty" >>"$LOG"
  exit 0
fi

if ! command -v agetty >/dev/null 2>&1; then
  echo "[login] agetty not installed; skipping console login" >>"$LOG"
  exit 0
fi

start_getty() {
  local tty="$1"
  [[ -c "/dev/$tty" ]] || return 0
  if pgrep -f "agetty.*$tty" >/dev/null 2>&1; then
    return 0
  fi
  echo "[login] starting agetty --autologin $USER on $tty" >>"$LOG"
  agetty --autologin "$USER" --noclear "$tty" linux >>"$LOG" 2>&1 &
}

start_getty tty1
start_getty ttyS0

touch /run/cog/login.started
echo "[login] metal console login ready" >>"$LOG"
