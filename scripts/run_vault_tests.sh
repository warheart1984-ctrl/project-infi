#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.venvs/project-infi/bin:${HOME}/.local/bin:${PATH}"
python -m pytest tests/test_vault_cp001.py -q
python scripts/cp001_category_b_closure.py --json
