#!/usr/bin/env bash
# CTS test suite entry — traceability + constitutional checks
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "[CTS-TESTS] Traceability chain validation"
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/validate_traceability_chain.py
elif command -v python >/dev/null 2>&1; then
  python scripts/validate_traceability_chain.py
else
  node scripts/validate_traceability_chain.mjs
fi

echo "[CTS-TESTS] Constitutional test suite"
bash cts/run_all.sh 2>/dev/null || node cts/run_all.mjs

echo "[CTS-TESTS] All tests passed"
