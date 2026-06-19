#!/usr/bin/env bash
# Start lawful brain + operator kernel for local development (Linux + macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
export OPERATOR_KERNEL_CONFIG="${OPERATOR_KERNEL_CONFIG:-${ROOT}/operator_kernel.config.yaml}"
export AAIS_SIGNING_SECRET="${AAIS_SIGNING_SECRET:-operator-kernel-dev-secret}"
export AAIS_WORKSPACE_ROOT="${AAIS_WORKSPACE_ROOT:-${ROOT}/.runtime/e2e-operator-workspace}"
export OPERATOR_AGENT_INTER_STEP_SLEEP_SEC="${OPERATOR_AGENT_INTER_STEP_SLEEP_SEC:-2}"
export OPERATOR_LAWFUL_PLANNER_FALLBACK="${OPERATOR_LAWFUL_PLANNER_FALLBACK:-1}"
export OPERATOR_E2E_CANCEL_WINDOW="${OPERATOR_E2E_CANCEL_WINDOW:-1}"

if [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
elif [[ -n "${OPERATOR_PYTHON:-}" && -x "${OPERATOR_PYTHON}" ]]; then
  PY="${OPERATOR_PYTHON}"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "Python 3.10+ required" >&2
  exit 1
fi

mkdir -p "${AAIS_WORKSPACE_ROOT}"

echo "Using Python: ${PY}"
echo "Starting lawful brain on 127.0.0.1:8791 ..."
"${PY}" -m operator_kernel.lawful_brain >/dev/null 2>&1 &
BRAIN_PID=$!

cleanup() {
  kill "${BRAIN_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2

echo "Starting operator kernel on 127.0.0.1:8790 ..."
exec "${PY}" -m operator_kernel
