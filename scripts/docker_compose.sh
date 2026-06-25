#!/usr/bin/env bash
# docker compose vs docker-compose compatibility (WSL Debian often lacks compose plugin).
set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi
if command -v docker-compose >/dev/null 2>&1; then
  exec docker-compose "$@"
fi
echo "Neither 'docker compose' nor 'docker-compose' found" >&2
exit 127
