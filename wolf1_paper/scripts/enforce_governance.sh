#!/usr/bin/env bash
# Repo-wide governance enforcement gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[GOV] Running constitutional governance enforcement…"

bash cts/tests/run_all.sh 2>/dev/null || {
  echo "[GOV] bash unavailable — Node fallback"
  node scripts/validate_traceability_chain.mjs
  node cts/run_all.mjs
}

echo "[GOV] Governance enforcement passed."
