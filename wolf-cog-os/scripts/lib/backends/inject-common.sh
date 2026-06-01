#!/usr/bin/env bash
# Shared inject-backend helpers for universal OS backends (P15).
set -euo pipefail

inject_apply_manifest() {
  local rootfs_out="$1"
  local manifest="${2:-${COGOS_INJECT_MANIFEST:-}}"

  if [[ -z "$manifest" || ! -f "$manifest" ]]; then
    echo "[inject] no manifest configured (COGOS_INJECT_MANIFEST); skipping"
    return 0
  fi

  COGOS_INJECT_ROOT="$rootfs_out" COGOS_INJECT_MANIFEST_PATH="$manifest" python3 - <<'PY'
import json
import os
import shutil
from pathlib import Path

root = Path(os.environ["COGOS_INJECT_ROOT"])
manifest = Path(os.environ["COGOS_INJECT_MANIFEST_PATH"])
spec = json.loads(manifest.read_text(encoding="utf-8"))
copies = spec.get("copy", [])
for entry in copies:
    src = Path(str(entry.get("src", "")))
    if not src.is_absolute():
        src = Path.cwd() / src
    dest = root / str(entry.get("dest", "")).lstrip("/")
    if not src.exists():
        raise SystemExit(f"inject source missing: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest)
print(f"[inject] applied manifest: {manifest} copies={len(copies)}")
PY
}

inject_mark_extracted() {
  local rootfs_out="$1"
  local platform="$2"
  mkdir -p "$rootfs_out"
  cat >"$rootfs_out/.forge-substrate-extracted" <<EOF
platform=$platform
extracted_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
}
