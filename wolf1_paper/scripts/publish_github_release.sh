#!/usr/bin/env bash
set -euo pipefail

DOC_ID="${1:-wolf1-arch}"
BUILD_DIR="${2:-build}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TAG="${GITHUB_REF_NAME:-$(git describe --tags --exact-match 2>/dev/null || true)}"
if [ -z "$TAG" ]; then
  echo "[GITHUB] SKIP: no release tag on current ref"
  exit 0
fi

VERSION=$(node -e "
  const { parse } = require('yaml');
  const fs = require('fs');
  const m = parse(fs.readFileSync('.governance/version.yaml','utf8'));
  console.log(m.documents.find(x => x.id === process.argv[1]).current_version);
" "$DOC_ID")

PDF="build/wolf1_v1.1-${VERSION}.pdf"
if [ ! -f "$PDF" ]; then
  echo "[GITHUB] ERROR: missing $PDF"
  exit 1
fi

if command -v gh >/dev/null 2>&1; then
  gh release create "$TAG" "$PDF" --notes-file CHANGELOG.md --title "WOLF-1 Architecture ${VERSION}"
else
  echo "[GITHUB] gh CLI not found — skipping release create"
fi
