#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="${1:-ci-artifacts}"
SIGNING_REQUIRED="${SIGNING_REQUIRED:-1}"
MINISIGN_KEY_FILE="${MINISIGN_KEY_FILE:-}"
MINISIGN_SECRET_KEY="${MINISIGN_SECRET_KEY:-}"

if [[ ! -d "$ARTIFACT_DIR" ]]; then
  echo "Artifact directory not found: $ARTIFACT_DIR" >&2
  exit 2
fi

if ! command -v minisign >/dev/null 2>&1; then
  echo "minisign not available." >&2
  exit 2
fi

tmp_key=""
cleanup() {
  [[ -n "$tmp_key" && -f "$tmp_key" ]] && rm -f "$tmp_key"
}
trap cleanup EXIT

if [[ -n "$MINISIGN_KEY_FILE" && -f "$MINISIGN_KEY_FILE" ]]; then
  key_file="$MINISIGN_KEY_FILE"
elif [[ -n "$MINISIGN_SECRET_KEY" ]]; then
  tmp_key="$(mktemp)"
  printf '%s\n' "$MINISIGN_SECRET_KEY" >"$tmp_key"
  chmod 600 "$tmp_key"
  key_file="$tmp_key"
else
  if [[ "$SIGNING_REQUIRED" == "1" ]]; then
    echo "No minisign private key provided." >&2
    exit 3
  fi
  echo "No key provided; skipping signing."
  exit 0
fi

manifest="$ARTIFACT_DIR/artifact-manifest.json"
python3 - <<'PY' "$ARTIFACT_DIR" "$manifest"
import hashlib
import json
import sys
from pathlib import Path

artifact_dir = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
records = []
for p in sorted(artifact_dir.glob("*")):
    if p.is_file() and not p.name.endswith(".minisig"):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        records.append({"name": p.name, "size_bytes": p.stat().st_size, "sha256": h})

manifest_path.write_text(json.dumps({"artifacts": records}, indent=2) + "\n", encoding="utf-8")
PY

while IFS= read -r file; do
  minisign -S -s "$key_file" -m "$file" -x "$file.minisig" -t "CoGOS artifact signature"
done < <(find "$ARTIFACT_DIR" -maxdepth 1 -type f \( -name '*.iso' -o -name '*.sha256' -o -name 'artifact-manifest.json' \))

echo "Signing complete for artifacts in $ARTIFACT_DIR"
