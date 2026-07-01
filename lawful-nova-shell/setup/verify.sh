#!/usr/bin/env bash
# Verify Lawful Nova local slice (Linux + macOS).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

WARN=0
FAIL=0

ok() { echo "[OK] $*"; }
info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; WARN=$((WARN + 1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL + 1)); }

get_candidate_repo_roots() {
  local shell_root
  shell_root="$(lawful_nova_shell_root)"
  printf '%s\n' "${LAWFUL_NOVA_REPO_ROOT:-}" "${shell_root}" "$(cd "${shell_root}/.." && pwd)"
}

get_repo_python() {
  lawful_nova_python
}

get_repo_nova_cli() {
  local shell_root
  shell_root="$(lawful_nova_shell_root)"
  printf '%s\n' "${NOVA_CLI:-${shell_root}/bin/nova}"
}

REPO_ROOT="$(lawful_nova_repo_root)"
lawful_nova_export_paths
lawful_nova_load_stack

echo "=== Lawful Nova verify (unix) ==="
echo "Repo: ${REPO_ROOT}"

PY="$(lawful_nova_python)" || fail "Python 3.10+"
if [[ "${PY}" == "${REPO_ROOT}/.venv/bin/python" && -x "${PY}" ]]; then
  ok "Python .venv ${PY}"
else
  warn "Python not from repo .venv: ${PY}"
fi

NOVA_SHIM="$(get_repo_nova_cli)"
if [[ -x "${NOVA_SHIM}" ]]; then
  ok "Nova CLI repo shim reachable ${NOVA_SHIM}"
else
  fail "Nova CLI repo shim missing or not executable ${NOVA_SHIM}"
fi

if [[ -d "${NOVA_CORTEX_PATH}" ]]; then
  ok "Cortex path ${NOVA_CORTEX_PATH}"
else
  fail "Missing cortex path ${NOVA_CORTEX_PATH}"
fi

if [[ -d "${NOVA_VOSS_RUNTIME_PATH}" ]]; then
  ok "Voss path ${NOVA_VOSS_RUNTIME_PATH}"
else
  fail "Missing voss path ${NOVA_VOSS_RUNTIME_PATH}"
fi

if [[ -d "${NOVA_RSL_PATH}" ]]; then
  ok "RSL path ${NOVA_RSL_PATH}"
else
  warn "RSL path not found ${NOVA_RSL_PATH}"
fi

if command -v docker >/dev/null 2>&1; then
  ok "Docker available"
else
  info "Docker not found - optional for native unix agent"
fi

if lawful_nova_http_health "${NOVA_API_URL}" >/dev/null 2>&1; then
  ok "Nova API ${NOVA_API_URL}/health"
else
  warn "Nova API not reachable at ${NOVA_API_URL} (start: scripts/start-nova-stack.sh --api-only)"
fi

if "${PY}" -m nova.cli health --json >/dev/null 2>&1; then
  ok "Direct LawfulLLM in-process"
else
  fail "nova.cli health failed"
fi

if [[ "${FAIL}" -gt 0 ]]; then
  echo "Verify failed (${FAIL} critical, ${WARN} warnings)"
  exit 1
fi

echo "Verify passed (${WARN} warnings)"
exit 0
