#!/usr/bin/env bash
# Source in bash/zsh:  source /path/to/project-infi/lawful-nova-shell/setup/novrc.sh
# Adds Lawful Nova LLM shell helpers (Linux + macOS).

_lawful_nova_novrc_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
# shellcheck source=lib/common.sh
source "${_lawful_nova_novrc_dir}/lib/common.sh"

lawful_nova_export_paths
lawful_nova_load_stack 2>/dev/null || true

export NOVA_CLI="${_lawful_nova_novrc_dir}/../bin/nova"

nova-chat() {
  "${NOVA_CLI}" chat "$@"
}

novr() {
  "${NOVA_CLI}" run "$@"
}

novtest() {
  "${_lawful_nova_novrc_dir}/verify.sh"
  "$(lawful_nova_python)" "${LAWFUL_NOVA_REPO_ROOT}/scripts/nova_productization_gate.py"
}

novpr() {
  "$(lawful_nova_python)" "${LAWFUL_NOVA_REPO_ROOT}/scripts/nova_productization_gate.py" "$@"
}

novdoc() {
  local doc="${LAWFUL_NOVA_REPO_ROOT}/docs/runtime/NOVA_LAWFUL_PRODUCTIZATION.md"
  if command -v open >/dev/null 2>&1; then
    open "${doc}"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${doc}"
  else
    cat "${doc}"
  fi
}

novsec() {
  "${NOVA_CLI}" health --json
}

novstack() {
  "${LAWFUL_NOVA_REPO_ROOT}/scripts/start-nova-stack.sh" "$@"
}

echo "[Nova] Lawful Nova shell ready (bash)."
echo "   nova-chat | novr | novtest | novpr | novdoc | novsec | novstack"
