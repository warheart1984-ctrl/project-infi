#!/usr/bin/env bash
# Shared Forge pipeline env + post-build hooks (P10-P14 wiring).
set -euo pipefail

forge_pipeline_lib_dir() {
  echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
}

forge_pipeline_load_env() {
  local pipeline="${1:?pipeline yaml required}"
  local lib_dir
  lib_dir="$(forge_pipeline_lib_dir)"
  if [[ ! -f "$pipeline" ]]; then
    echo "ERROR: pipeline spec not found: $pipeline" >&2
    return 3
  fi
  # shellcheck disable=SC1090
  eval "$(python3 "$lib_dir/resolve-pipeline-env.py" "$pipeline")"
  export COGOS_FORGE_PIPELINE="$pipeline"
}

forge_pipeline_replay_adapter() {
  local validation_json="${1:-${COGOS_CI_ARTIFACT_DIR:-ci-artifacts}/substrate-validation.json}"
  if [[ ! -f "$validation_json" ]]; then
    echo ""
    return 0
  fi
  python3 - <<PY
import json
print(json.load(open("$validation_json", encoding="utf-8")).get("replay_adapter", ""))
PY
}

forge_pipeline_emit_lineage() {
  local pipeline="${1:-${COGOS_FORGE_PIPELINE:-}}"
  local output_dir="${2:-${COGOS_CI_ARTIFACT_DIR:-ci-artifacts}}"
  local profile="${3:-${COGOS_FORGE_PROFILE:-forge-selfhosted}}"
  local replay_adapter="${4:-$(forge_pipeline_replay_adapter "$output_dir/substrate-validation.json")}"
  local emitter=""
  local lib_dir
  lib_dir="$(forge_pipeline_lib_dir)"

  for candidate in \
    "${FORGE_ROOT:-}/scripts/build/emit-forge-lineage.py" \
    "$lib_dir/../emit-forge-lineage.py"; do
    if [[ -f "$candidate" ]]; then
      emitter="$candidate"
      break
    fi
  done
  if [[ -z "$emitter" ]]; then
    echo "ERROR: emit-forge-lineage.py not found" >&2
    return 3
  fi

  local -a cmd=(
    python3 "$emitter"
    --pipeline "$pipeline"
    --profile "$profile"
    --rootfs-backend "${COGOS_ROOTFS_BACKEND:-debootstrap}"
    --substrate-id "${COGOS_SUBSTRATE_ID:-auto}"
    --output "$output_dir/forge-lineage.json"
  )
  if [[ -n "$replay_adapter" ]]; then
    cmd+=(--replay-adapter "$replay_adapter")
  fi
  if [[ -n "${COGOS_TAG:-}" ]]; then
    cmd+=(--cogos-tag "$COGOS_TAG")
  fi
  "${cmd[@]}"
}

forge_pipeline_emit_cloud_outputs() {
  local iso_path="${1:?iso path required}"
  local pipeline="${2:-${COGOS_FORGE_PIPELINE:-wolf-cog-os/forge/pipelines/daily-driver.yaml}}"
  local out_dir="${3:-${COGOS_CI_ARTIFACT_DIR:-ci-artifacts}/cloud}"
  local lib_dir script_dir
  lib_dir="$(forge_pipeline_lib_dir)"
  script_dir="$(cd "$lib_dir/.." && pwd)"

  if [[ -z "${COGOS_PIPELINE_CLOUD_FORMATS:-}" ]]; then
    forge_pipeline_load_env "$pipeline"
  fi
  if [[ -z "${COGOS_PIPELINE_CLOUD_FORMATS:-}" ]]; then
    echo "pipeline cloud outputs: none declared in $pipeline"
    return 0
  fi

  # shellcheck source=emit-pipeline-outputs.sh
  source "$script_dir/lib/emit-pipeline-outputs.sh"
  SCRIPT_DIR="$script_dir"
  emit_pipeline_outputs "$iso_path" "$pipeline" "$out_dir"
}

forge_pipeline_maybe_build_rootfs() {
  local profile="${1:-${COGOS_FORGE_PROFILE:-forge-selfhosted}}"
  local script_dir
  script_dir="$(cd "$(forge_pipeline_lib_dir)/.." && pwd)"
  local backend="${COGOS_ROOTFS_BACKEND:-debootstrap}"

  if [[ "${COGOS_BUILD_FROM_TREE:-0}" != "1" ]]; then
    return 0
  fi
  if [[ "$backend" == "debootstrap" && "${COGOS_PIPELINE_FORCE_ROOTFS:-0}" != "1" ]]; then
    return 0
  fi

  echo "[pipeline] building rootfs with backend=$backend profile=$profile"
  if [[ "$(id -u)" -eq 0 ]]; then
    bash "$script_dir/build-rootfs.sh" --profile "$profile"
  else
    sudo bash "$script_dir/build-rootfs.sh" --profile "$profile"
  fi
}
