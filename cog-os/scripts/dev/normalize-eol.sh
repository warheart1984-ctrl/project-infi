#!/usr/bin/env bash
# Renormalize line endings per repo-root .gitattributes (prefer over destructive git reset --hard).
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [[ ! -f .gitattributes ]]; then
  echo "Missing .gitattributes at repo root; add one before renormalizing." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes; renormalize may touch many files." >&2
  echo "Review with: git diff --stat" >&2
fi

echo "Running: git add --renormalize ."
git add --renormalize .

echo "Done. Inspect with: git diff --cached --stat"
