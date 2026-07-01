#!/usr/bin/env bash
set -euo pipefail

DOC_ID="${1:-wolf1-arch}"
cd "$(dirname "$0")"

export DOC_ID
node build.mjs "$DOC_ID"
