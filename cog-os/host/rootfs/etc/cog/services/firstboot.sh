#!/bin/bash
# One-shot firstboot — runs when pending marker exists.
set -euo pipefail

MARKER=/run/cog/firstboot.pending
DONE=/run/cog/firstboot.done
LIB=/usr/lib/cogos/cogos-firstboot-invariants.sh

if [[ -f "$DONE" ]]; then
  exit 0
fi

if [[ ! -f "$MARKER" && ! -f /opt/cogos/memory/operator/FIRST_BOOT_PENDING ]]; then
  exit 0
fi

mkdir -p /run/cog /var/log/cog
if [[ -x "$LIB" ]]; then
  COG_PROFILE="${COG_PROFILE:-metal}" bash "$LIB"
else
  echo "[firstboot] invariants script missing; applying minimal marker cleanup" >>/var/log/cog/init.log
  rm -f /opt/cogos/memory/operator/FIRST_BOOT_PENDING 2>/dev/null || true
fi

date -Iseconds >"$DONE"
rm -f "$MARKER"
