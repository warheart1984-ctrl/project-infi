#!/usr/bin/env bash
# Seed the local LSG JSONL store from the core YAML bundle.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${LAWFUL_NOVA_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"

export LAWFUL_NOVA_REPO_ROOT="${REPO_ROOT}"
export NOVA_LSG_PATH="${NOVA_LSG_PATH:-${REPO_ROOT}/lsg/LSG-CORE.v1.yaml}"
export NOVA_LSG_STORE="${NOVA_LSG_STORE:-${HOME}/.nova/lsg/local.jsonl}"

PYTHON="${PYTHON:-python3}"
if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON="${REPO_ROOT}/.venv/bin/python"
fi

echo "[nova-bootstrap-lsg] bundle=${NOVA_LSG_PATH}"
echo "[nova-bootstrap-lsg] store=${NOVA_LSG_STORE}"

"${PYTHON}" - <<'PY'
from nova.lsg_loader import load_lsg_bundle, default_lsg_bundle_path, default_lsg_store_path

result = load_lsg_bundle(default_lsg_bundle_path(), store_path=default_lsg_store_path())
print(result)
PY
