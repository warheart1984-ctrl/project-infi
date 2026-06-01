#!/usr/bin/env bash
# Forge replay adapter dispatcher (P10).
set -euo pipefail

replay_adapter_registry() {
  echo "${COGOS_REPLAY_ADAPTER_REGISTRY:-$WOLF_FORGE_STAGING/replay-adapters/registry.json}"
}

replay_adapter_detect() {
  local iso_path="${1:-${COGOS_SUBSTRATE_ISO:-}}"
  if [[ -n "${COGOS_REPLAY_ADAPTER:-}" ]]; then
    return 0
  fi
  if [[ -n "$iso_path" && -f "$iso_path" && -f "$REPO_ROOT/wolf-cog-os/scripts/validate-substrate.py" ]]; then
    local out="${COGOS_CI_ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts}/substrate-detect-tmp.json"
    mkdir -p "$(dirname "$out")"
    if python3 "$REPO_ROOT/wolf-cog-os/scripts/validate-substrate.py" \
      --iso "$iso_path" \
      --substrate-id "${COGOS_SUBSTRATE_ID:-auto}" \
      --mode warn \
      --output "$out" >/dev/null 2>&1; then
      local detected
      detected="$(python3 -c "import json; print(json.load(open('$out', encoding='utf-8')).get('replay_adapter',''))" 2>/dev/null || true)"
      if [[ -n "$detected" ]]; then
        export COGOS_REPLAY_ADAPTER="$detected"
        return 0
      fi
    fi
  fi
  export COGOS_REPLAY_ADAPTER="${COGOS_REPLAY_ADAPTER:-debian-live-layout}"
}

replay_adapter_module() {
  local adapter="${COGOS_REPLAY_ADAPTER:-debian-live-layout}"
  local module="${SCRIPT_DIR}/lib/replay-adapters/${adapter}.sh"
  if [[ ! -f "$module" ]]; then
    echo "ERROR: replay adapter module missing: $adapter ($module)" >&2
    return 3
  fi
  # shellcheck source=/dev/null
  source "$module"
}

replay_resolve_sfs() {
  local work_iso="$1"
  replay_adapter_module
  adapter_resolve_sfs "$work_iso"
}

replay_sfs_write_path() {
  local work_iso="$1"
  replay_adapter_module
  adapter_sfs_write_path "$work_iso"
}

replay_workdir_ready() {
  local work="$1"
  replay_adapter_module
  adapter_workdir_ready "$work"
}

replay_extract_rootfs() {
  local work_iso="$1"
  local rootfs_out="$2"
  replay_adapter_module
  adapter_extract_rootfs "$work_iso" "$rootfs_out"
}
