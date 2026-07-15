#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "${SCRIPT_DIR}/.." && pwd)"
shell_root="${repo}/lawful-nova-shell"

if [[ ! -d "${shell_root}" ]]; then
  echo "Missing lawful-nova-shell at ${shell_root}" >&2
  exit 1
fi

# shellcheck source=../lawful-nova-shell/setup/lib/common.sh
source "${shell_root}/setup/lib/common.sh"
PY="$(lawful_nova_python)"

port_available() {
  local port="$1"
  "${PY}" - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket()
try:
    sock.bind(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

preferred_port="${NOVA_PORT:-8080}"
if ! port_available "${preferred_port}"; then
  for candidate in 8080 8081 8082; do
    if port_available "${candidate}"; then
      preferred_port="${candidate}"
      break
    fi
  done
fi

export NOVA_PORT="${preferred_port}"
unset NOVA_API_URL
lawful_nova_export_paths

PY="$(lawful_nova_python)"

health_ok() {
  lawful_nova_http_health "${NOVA_API_URL}" >/dev/null 2>&1
}

if health_ok; then
  echo "[Nova] API already reachable at ${NOVA_API_URL}/health"
  exit 0
fi

echo "[Nova] Starting Nova API at ${NOVA_API_URL}"
(cd "${shell_root}" && "${PY}" -m nova.api) >/tmp/nova-api.log 2>&1 &
api_pid=$!

ready=0
for _ in $(seq 1 20); do
  sleep 1
  if health_ok; then
    ready=1
    break
  fi
done

if [[ "${ready}" -ne 1 ]]; then
  echo "Nova API did not become healthy at ${NOVA_API_URL}/health" >&2
  echo "Log: /tmp/nova-api.log" >&2
  exit 1
fi

echo "[Nova] API ready at ${NOVA_API_URL}/health (pid ${api_pid})"

if [[ "${1:-}" == "--api-only" ]]; then
  exit 0
fi

if [[ -f "${shell_root}/desktop/package.json" ]] && command -v npm >/dev/null 2>&1; then
  (cd "${shell_root}/desktop" && npm start)
else
  echo "[Nova] Desktop not started. Run 'cd ${shell_root}/desktop && npm start' if you want the UI."
fi
