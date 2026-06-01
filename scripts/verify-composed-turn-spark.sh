#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Spark v1: constitutional pipeline =="
python -m pytest tests/test_spark_pipeline.py tests/test_coherence_projection.py -q

echo "== Spark v1: composed turn backend =="
python -m pytest tests/test_aais_composed_runtime.py -q

echo "== Spark v1: memory board cues =="
python -m pytest tests/test_memory_runtime.py -k memory_board -q

echo "== Spark v1: compose receipt helpers present =="
test -f frontend/src/lib/composeReceipt.js
test -f frontend/src/components/ComposeReceiptPanel.jsx

echo "Spark v1 verification complete (asserted, single machine)."
