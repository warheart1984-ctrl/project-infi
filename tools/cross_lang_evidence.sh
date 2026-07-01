#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RECEIPT_JSON="${TMPDIR:-/tmp}/receipt.json"
STDERR_LOG="${TMPDIR:-/tmp}/aaes-cas-evidence.stderr"

cd "$ROOT"

# 1. Run Rust evidence harness → JSON on stdout, RUST_HASH on stderr
cargo run -q -p aaes-cas-evidence >"$RECEIPT_JSON" 2>"$STDERR_LOG"
RUST_HASH="$(grep -E '^RUST_HASH=' "$STDERR_LOG" | head -n1 | cut -d= -f2-)"

# 2. Run Python evidence harness on same JSON
PY_HASH="$(python bindings/python/evidence_harness.py "$RECEIPT_JSON" 2>&1 | grep -E '^PY_HASH=' | head -n1 | cut -d= -f2-)"

echo "RUST_HASH=$RUST_HASH"
echo "PY_HASH=$PY_HASH"

if [ -z "$RUST_HASH" ] || [ -z "$PY_HASH" ]; then
  echo "❌ Failed to capture cross-language hashes"
  exit 1
fi

if [ "$RUST_HASH" != "$PY_HASH" ]; then
  echo "❌ Cross-language hash mismatch"
  exit 1
fi

echo "✅ Cross-language CAS receipt hash is stable across Rust and Python"
