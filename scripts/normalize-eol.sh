#!/usr/bin/env bash
# Renormalize line endings per .gitattributes (prefer over destructive git reset --hard).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not a git repository: $REPO_ROOT" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes; renormalize may touch many files." >&2
  echo "Review with: git diff --stat" >&2
fi

echo "Running: git add --renormalize ."
git add --renormalize .

echo "Done. Inspect with: git diff --cached --stat"
