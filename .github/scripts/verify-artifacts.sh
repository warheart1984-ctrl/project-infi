#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="${1:-ci-artifacts}"
MINISIGN_PUBLIC_KEY="${MINISIGN_PUBLIC_KEY:-}"
MINISIGN_PUBLIC_KEY_FILE="${MINISIGN_PUBLIC_KEY_FILE:-}"

if [[ ! -d "$ARTIFACT_DIR" ]]; then
  echo "Artifact directory not found: $ARTIFACT_DIR" >&2
  exit 2
fi

if ! command -v minisign >/dev/null 2>&1; then
  echo "minisign not available." >&2
  exit 2
fi

pub_file=""
tmp_pub=""
cleanup() {
  [[ -n "$tmp_pub" && -f "$tmp_pub" ]] && rm -f "$tmp_pub"
}
trap cleanup EXIT

if [[ -n "$MINISIGN_PUBLIC_KEY_FILE" && -f "$MINISIGN_PUBLIC_KEY_FILE" ]]; then
  pub_file="$MINISIGN_PUBLIC_KEY_FILE"
elif [[ -n "$MINISIGN_PUBLIC_KEY" ]]; then
  tmp_pub="$(mktemp)"
  printf '%s\n' "$MINISIGN_PUBLIC_KEY" >"$tmp_pub"
  pub_file="$tmp_pub"
else
  echo "No minisign public key provided." >&2
  exit 3
fi

if [[ ! -f "$ARTIFACT_DIR/artifact-manifest.json" ]]; then
  echo "artifact-manifest.json missing in $ARTIFACT_DIR" >&2
  exit 4
fi

python3 - <<'PY' "$ARTIFACT_DIR"
import hashlib
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
manifest = json.loads((base / "artifact-manifest.json").read_text(encoding="utf-8"))
for item in manifest.get("artifacts", []):
    p = base / item["name"]
    if not p.exists():
        raise SystemExit(f"Missing artifact listed in manifest: {item['name']}")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != item.get("sha256"):
        raise SystemExit(f"SHA mismatch for {item['name']}: {h} != {item.get('sha256')}")
print("Manifest checksums verified.")
PY

while IFS= read -r sig; do
  msg="${sig%.minisig}"
  [[ -f "$msg" ]] || { echo "Signed message missing for $sig" >&2; exit 5; }
  minisign -Vm "$msg" -x "$sig" -P "$(cat "$pub_file")"
done < <(find "$ARTIFACT_DIR" -maxdepth 1 -type f -name '*.minisig' | sort)

echo "Artifact signature verification complete."
