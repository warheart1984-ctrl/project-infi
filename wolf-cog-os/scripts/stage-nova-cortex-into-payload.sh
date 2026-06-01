#!/usr/bin/env bash
# Stage Nova Cortex (src/cog_runtime + bridge) into Wolf CoG OS payload cache.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"

stage_nova_cortex_into_payload() {
  local payload_cache="${1:-${COGOS_PAYLOAD_CACHE:-${HOME}/.cogos-payload-cache}}"
  local repo_payload="${2:-$WOLF_COGOS_ROOT/payload}"
  local runtime_root="$payload_cache/opt/cogos/runtime"
  local src_root="$runtime_root/src"

  echo "[nova-cortex] export family manifest → repo payload"
  bash "$REPO_ROOT/scripts/cogos/export-cognitive-runtime-family.sh" \
    "$repo_payload/opt/cogos/config/cognitive_runtime_family.json"

  [[ -d "$payload_cache/opt/cogos" ]] || {
    echo "ERROR: stage-nova-cortex: payload cache missing opt/cogos: $payload_cache" >&2
    echo "ERROR: run ensure_payload_ready first" >&2
    return 1
  }

  mkdir -p "$src_root" "$payload_cache/opt/cogos/config"

  echo "[nova-cortex] staging src/cog_runtime → $src_root/cog_runtime"
  rsync -a --delete \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    "$REPO_ROOT/src/cog_runtime/" "$src_root/cog_runtime/"

  touch "$src_root/__init__.py"

  for module in \
    cogos_runtime_bridge.py \
    aais_composed_runtime.py \
    aais_ul.py \
    aais_ul_substrate.py \
    direct_challenge_module.py \
    jarvis_reasoning_protocol.py \
    jarvis_types.py \
    reasoning_types.py; do
    if [[ -f "$REPO_ROOT/src/$module" ]]; then
      rsync -a "$REPO_ROOT/src/$module" "$src_root/"
    fi
  done

  if [[ -d "$REPO_ROOT/src/speaking_runtime" ]]; then
    echo "[nova-cortex] staging src/speaking_runtime"
    rsync -a --delete \
      --exclude '__pycache__/' \
      --exclude '*.pyc' \
      "$REPO_ROOT/src/speaking_runtime/" "$src_root/speaking_runtime/"
    touch "$src_root/speaking_runtime/__init__.py"
  fi

  cat > "$payload_cache/opt/cogos/config/nova_cortex.env" <<'EOF'
# Nova Cortex unified PYTHONPATH (Wolf CoG OS Full)
export PYTHONPATH="/opt/cogos/runtime:/opt/cogos/runtime/src${PYTHONPATH:+:$PYTHONPATH}"
export COGOS_NOVA_CORTEX=1
EOF
  install -D -m644 "$payload_cache/opt/cogos/config/nova_cortex.env" \
    "$repo_payload/opt/cogos/config/nova_cortex.env"

  local registry_src="$repo_payload/opt/cogos/memory/backups/bundle-20260526-034252-operator/config/governance_registry.json"
  local registry_dst="$payload_cache/opt/cogos/config/governance_registry.json"
  if [[ -f "$registry_src" && ! -f "$registry_dst" ]]; then
    install -D -m644 "$registry_src" "$registry_dst"
  fi

  cat > "$runtime_root/cogos_runtime_bridge.py" <<'PY'
"""Wolf CoG OS Nova Cortex bridge shim (PYTHONPATH=/opt/cogos/runtime:/opt/cogos/runtime/src)."""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path("/opt/cogos/runtime")
for candidate in (_root, _root / "src"):
    path = str(candidate)
    if path not in sys.path:
        sys.path.insert(0, path)

from src.cogos_runtime_bridge import *  # noqa: F403
PY

  bash "$SCRIPT_DIR/lib/normalize-boot-stack-lf.sh" "$payload_cache"

  echo "[nova-cortex] verify import from staged payload"
  PYTHONPATH="$runtime_root:$src_root" python3 <<PY
from src.cogos_runtime_bridge import family_spec
spec = family_spec()
assert spec.get("family_id") == "nova.cortex", spec.get("family_id")
print("nova.cortex", spec.get("version"), "staged OK")
PY

  echo "[nova-cortex] unified staging complete: $payload_cache"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  stage_nova_cortex_into_payload "${1:-}" "${2:-}"
fi
