#!/usr/bin/env bash
# Start Lawful Nova LLM stack (Linux + macOS).
# Usage:
#   ./scripts/start-nova-stack.sh              # API + operator stack
#   ./scripts/start-nova-stack.sh --api-only   # Nova API on :8080 only
#   ./scripts/start-nova-stack.sh --operator-only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

API_ONLY=0
OPERATOR_ONLY=0
PRESET="${AAIS_PRESET:-mock}"
START_AAIS=0

for arg in "$@"; do
  case "$arg" in
    --api-only) API_ONLY=1 ;;
    --operator-only) OPERATOR_ONLY=1 ;;
    --with-aais) START_AAIS=1 ;;
    --preset=*) PRESET="${arg#*=}" ;;
    -h|--help)
      echo "Usage: $0 [--api-only] [--operator-only] [--with-aais] [--preset=mock|laptop|default]"
      exit 0
      ;;
  esac
done

# shellcheck source=../lawful-nova-shell/setup/lib/common.sh
source "${ROOT}/lawful-nova-shell/setup/lib/common.sh"
export LAWFUL_NOVA_REPO_ROOT="${ROOT}"
lawful_nova_export_paths

PY="$(lawful_nova_python)"
PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    kill "${pid}" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

start_api() {
  if lawful_nova_http_health "${NOVA_API_URL}" >/dev/null 2>&1; then
    echo "Nova API already up at ${NOVA_API_URL}"
    return 0
  fi
  echo "Starting Nova API on ${NOVA_API_URL} ..."
  "${PY}" -m nova.api >/dev/null 2>&1 &
  PIDS+=("$!")
  sleep 2
  if lawful_nova_http_health "${NOVA_API_URL}" >/dev/null 2>&1; then
    echo "  OK ${NOVA_API_URL}/health"
  else
    echo "Nova API failed to start" >&2
    exit 1
  fi
}

start_operator() {
  export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
  export OPERATOR_KERNEL_CONFIG="${OPERATOR_KERNEL_CONFIG:-${ROOT}/operator_kernel.config.yaml}"
  export AAIS_SIGNING_SECRET="${AAIS_SIGNING_SECRET:-operator-kernel-dev-secret}"
  export AAIS_WORKSPACE_ROOT="${AAIS_WORKSPACE_ROOT:-${ROOT}/.runtime/e2e-operator-workspace}"
  mkdir -p "${AAIS_WORKSPACE_ROOT}"

  if lawful_nova_http_health "http://127.0.0.1:8791" >/dev/null 2>&1; then
    echo "Lawful brain already up on :8791"
  else
    echo "Starting lawful brain on 127.0.0.1:8791 ..."
    "${PY}" -m operator_kernel.lawful_brain >/dev/null 2>&1 &
    PIDS+=("$!")
    sleep 2
  fi

  if lawful_nova_http_health "http://127.0.0.1:8790" >/dev/null 2>&1; then
    echo "Operator kernel already up on :8790"
  else
    echo "Starting operator kernel on 127.0.0.1:8790 ..."
    "${PY}" -m operator_kernel >/dev/null 2>&1 &
    PIDS+=("$!")
    sleep 2
  fi
}

start_aais() {
  echo "Starting AAIS (preset=${PRESET}) ..."
  exec "${PY}" -m aais start --data-dir "${ROOT}/.runtime/aais-data" --preset "${PRESET}" --no-browser --port 8000
}

if [[ "${OPERATOR_ONLY}" -eq 1 ]]; then
  start_operator
elif [[ "${API_ONLY}" -eq 1 ]]; then
  start_api
else
  start_api
  start_operator
fi

echo ""
echo "Lawful Nova stack running:"
echo "  Nova API:         ${NOVA_API_URL}/health"
echo "  Lawful brain:     http://127.0.0.1:8791/health"
echo "  Operator kernel:  http://127.0.0.1:8790/health"
echo ""
echo "CLI: ${ROOT}/lawful-nova-shell/bin/nova health --json"
echo "Press Ctrl+C to stop background services."
echo ""

if [[ "${START_AAIS}" -eq 1 ]]; then
  start_aais
fi

wait
