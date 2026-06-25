#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.venvs/project-infi/bin:${HOME}/.local/bin:${PATH}"
exec ./scripts/ci_http_stack_proof.sh
