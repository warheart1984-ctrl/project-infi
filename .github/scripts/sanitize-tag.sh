#!/usr/bin/env bash
set -euo pipefail

raw="${1:-}"
if [[ -z "$raw" ]]; then
  raw="untagged"
fi

# Lowercase, keep filename-safe chars, collapse separators.
sanitized="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]')"
sanitized="$(printf '%s' "$sanitized" | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//; s/-{2,}/-/g')"

if [[ -z "$sanitized" ]]; then
  sanitized="untagged"
fi

# Keep artifact names manageable.
printf '%s\n' "${sanitized:0:64}"
