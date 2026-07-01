#!/usr/bin/env bash
# Governance Receipt Generator — delegates to Node for traceability-aware receipts.
set -euo pipefail

DOC_ID="${1:-}"
BUILD_DIR="${2:-build}"

if [ -z "$DOC_ID" ]; then
  echo "Usage: gen_build_receipt.sh <doc-id> [build-dir]"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v node >/dev/null 2>&1; then
  exec node scripts/gen_build_receipt.mjs "$DOC_ID" "$BUILD_DIR"
fi

echo "[RECEIPT][FAIL] Node.js required for receipt generation (traceability block)"
exit 1
