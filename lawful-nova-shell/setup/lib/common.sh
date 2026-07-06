#!/usr/bin/env bash
# Shared helpers for Lawful Nova shell (Linux + macOS).

set -euo pipefail

lawful_nova_shell_root() {
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here/../.." && pwd
}

lawful_nova_is_repo_root() {
  local candidate="$1"
  [[ -f "${candidate}/pyproject.toml" && -d "${candidate}/nova" ]]
}

lawful_nova_candidate_repo_roots() {
  local shell_root cwd parent
  shell_root="$(lawful_nova_shell_root)"
  parent="$(cd "${shell_root}/.." && pwd)"
  cwd="$(pwd)"

  [[ -n "${LAWFUL_NOVA_REPO_ROOT:-}" ]] && printf '%s\n' "${LAWFUL_NOVA_REPO_ROOT}"
  printf '%s\n' "${shell_root}"
  printf '%s\n' "${parent}"
  printf '%s\n' "${cwd}"
}

lawful_nova_repo_root() {
  local candidate resolved seen=""
  while IFS= read -r candidate; do
    [[ -n "${candidate}" && -d "${candidate}" ]] || continue
    resolved="$(cd "${candidate}" && pwd)"
    case ":${seen}:" in
      *":${resolved}:"*) continue ;;
    esac
    seen="${seen}:${resolved}"
    if lawful_nova_is_repo_root "${resolved}"; then
      echo "${resolved}"
      return 0
    fi
  done < <(lawful_nova_candidate_repo_roots)

  echo "Lawful Nova repo root not found (set LAWFUL_NOVA_REPO_ROOT)" >&2
  return 1
}

lawful_nova_python() {
  local repo py
  repo="$(lawful_nova_repo_root)"
  py="${repo}/.venv/bin/python"
  if [[ -x "${py}" ]]; then
    echo "${py}"
    return 0
  fi
  if [[ -n "${OPERATOR_PYTHON:-}" && -x "${OPERATOR_PYTHON}" ]]; then
    echo "${OPERATOR_PYTHON}"
    return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null && {
      echo python3
      return 0
    }
  fi
  echo "Python 3.10+ or repo .venv required (run: python3 -m venv .venv && pip install -e '.[dev]')" >&2
  return 1
}

lawful_nova_load_stack() {
  local shell_root config
  shell_root="$(lawful_nova_shell_root)"
  config="${shell_root}/config/nova/nova-stack.json"
  if [[ ! -f "${config}" ]]; then
    echo "Missing stack config: ${config}" >&2
    return 1
  fi
  LAWFUL_NOVA_STACK_CONFIG="${config}"
  export LAWFUL_NOVA_STACK_CONFIG
}

lawful_nova_export_paths() {
  local repo
  repo="$(lawful_nova_repo_root)"
  export LAWFUL_NOVA_REPO_ROOT="${repo}"
  export NOVA_CORTEX_PATH="${NOVA_CORTEX_PATH:-${repo}/nova}"
  export NOVA_VOSS_RUNTIME_PATH="${NOVA_VOSS_RUNTIME_PATH:-${repo}/nova}"
  export NOVA_RSL_PATH="${NOVA_RSL_PATH:-${repo}/governance}"
  export NOVA_API_URL="${NOVA_API_URL:-http://127.0.0.1:${NOVA_PORT:-8080}}"
  export NOVA_CLI="${NOVA_CLI:-$(lawful_nova_shell_root)/bin/nova}"
  export PYTHONPATH="${repo}${PYTHONPATH:+:${PYTHONPATH}}"
}

lawful_nova_http_health() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS "${url%/}/health" 2>/dev/null
    return $?
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<PY
import urllib.request
import sys
try:
    with urllib.request.urlopen("${url%/}/health", timeout=2) as r:
        sys.stdout.write(r.read().decode())
except OSError:
    sys.exit(1)
PY
    return $?
  fi
  return 1
}
