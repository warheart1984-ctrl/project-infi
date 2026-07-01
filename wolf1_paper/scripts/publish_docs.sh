#!/usr/bin/env bash
set -euo pipefail

DOC_ID="${1:-wolf1-arch}"
BUILD_DIR="${2:-build}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DOCS_OUT="${DOCS_PORTAL_DIR:-docs-portal/build}"
mkdir -p "$DOCS_OUT"

cp -f build/wolf1_v1.1-*.pdf "$DOCS_OUT/" 2>/dev/null || true
cp -f build/wolf1_v1.1-*.html "$DOCS_OUT/" 2>/dev/null || true
cp -f CHANGELOG.md "$DOCS_OUT/" 2>/dev/null || true
cp -f governance/dashboard.html "$DOCS_OUT/" 2>/dev/null || true
cp -f governance/dashboard-loader.js "$DOCS_OUT/" 2>/dev/null || true
cp -f governance/receipts-index.json "$DOCS_OUT/" 2>/dev/null || true

echo "[DOCS] Staged artifacts in $DOCS_OUT"
echo "[DOCS] Wire CI to publish docs-portal/ to GitHub Pages or your portal host"
