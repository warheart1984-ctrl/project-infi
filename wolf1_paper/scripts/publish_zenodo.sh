#!/usr/bin/env bash
# Publish to Zenodo when ZENODO_TOKEN is set and git tag matches document version.
set -euo pipefail

DOC_ID="${1:-wolf1-arch}"
BUILD_DIR="${2:-build}"
META_DIR="${3:-metadata}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -z "${ZENODO_TOKEN:-}" ]; then
  echo "[ZENODO] SKIP: ZENODO_TOKEN not set"
  exit 0
fi

VERSION=$(node -e "
  const { parse } = require('yaml');
  const fs = require('fs');
  const m = parse(fs.readFileSync('.governance/version.yaml','utf8'));
  const d = m.documents.find(x => x.id === process.argv[1]);
  console.log(d.current_version);
" "$DOC_ID")

PDF="build/wolf1_v1.1-${VERSION}.pdf"
META="${META_DIR}/zenodo.json"

if [ ! -f "$PDF" ]; then
  echo "[ZENODO] ERROR: missing $PDF — run make pdf first"
  exit 1
fi

echo "[ZENODO] Would upload $PDF with metadata $META"
echo "[ZENODO] Implement deposition create + file attach via Zenodo API v2"
# curl -H "Authorization: Bearer $ZENODO_TOKEN" ...
