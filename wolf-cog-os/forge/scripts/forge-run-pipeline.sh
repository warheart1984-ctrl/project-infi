#!/usr/bin/env bash
# Run a Forge pipeline spec from inside Forge Mode.
set -euo pipefail

FORGE_ROOT="${FORGE_ROOT:-/forge}"
PIPELINE="${1:-}"
REPO_ROOT="${REPO_ROOT:-/forge}"
STAGE_LIB="${FORGE_ROOT}/scripts/build/lib/forge-pipeline-run.sh"
HOST_LIB="${REPO_ROOT}/wolf-cog-os/scripts/lib/forge-pipeline-run.sh"

usage() {
  cat <<USAGE
Usage:
  forge-run-pipeline.sh <pipeline.yaml>

Runs a Forge variant pipeline using staged build wrappers under ${FORGE_ROOT}/scripts/build/.
Set COGOS_SUBSTRATE_ISO to any compatible live hybrid ISO (OS-agnostic replay substrate).
USAGE
}

if [[ -z "$PIPELINE" ]]; then
  usage >&2
  exit 2
fi

if [[ -f "$STAGE_LIB" ]]; then
  # shellcheck source=/dev/null
  source "$STAGE_LIB"
elif [[ -f "$HOST_LIB" ]]; then
  # shellcheck source=/dev/null
  source "$HOST_LIB"
else
  echo "ERROR: forge-pipeline-run.sh library missing" >&2
  exit 4
fi

if [[ ! -f "$PIPELINE" ]]; then
  echo "ERROR: pipeline spec not found: $PIPELINE" >&2
  exit 3
fi

forge_pipeline_load_env "$PIPELINE"

output_dir="${FORGE_ROOT}/output/${COGOS_PIPELINE_NAME:-variant}"
mkdir -p "$output_dir" "${FORGE_ROOT}/cache"
export COGOS_CI_ARTIFACT_DIR="$output_dir"
export COGOS_FORGE_PROFILE="${COGOS_FORGE_PROFILE:-forge-selfhosted}"
export COGOS_BOOT_PROFILE=forge
export COGOS_BUILD_FROM_TREE=1
export COGOS_GRUB_MERGE=1
export COGOS_ENABLE_PID1=0
export COGOS_OUT="${COGOS_OUT:-$output_dir/${COGOS_PIPELINE_ISO_NAME:-cogos-${COGOS_PIPELINE_NAME:-variant}.iso}}"

if [[ -n "${COGOS_PIPELINE_ISO:-}" ]]; then
  export COGOS_SUBSTRATE_ISO="$COGOS_PIPELINE_ISO"
fi

echo "=== Forge pipeline: ${COGOS_PIPELINE_NAME:-unknown} ==="
echo "Spec:     $PIPELINE"
echo "Backend:  ${COGOS_ROOTFS_BACKEND:-debootstrap}"
echo "Cloud:    ${COGOS_PIPELINE_CLOUD_FORMATS:-<none>}"
echo "Output:   $COGOS_OUT"
echo "Profile:  $COGOS_FORGE_PROFILE"
echo "Substrate id: ${COGOS_SUBSTRATE_ID:-auto}"

build_wrapper="${FORGE_ROOT}/scripts/build/build.sh"
validate_substrate="${FORGE_ROOT}/scripts/build/validate-substrate.py"
registry="${FORGE_ROOT}/substrates/registry.json"
if [[ ! -f "$build_wrapper" ]]; then
  echo "ERROR: staged build wrapper missing: $build_wrapper" >&2
  exit 4
fi
chmod +x "$build_wrapper" 2>/dev/null || true

replay_iso="${COGOS_SUBSTRATE_ISO:-${COGOS_BOOT_REPLAY_ISO:-${COGOS_DEBIAN_ISO:-}}}"
substrate_lib="${FORGE_ROOT}/scripts/build/lib/substrate-resolve.sh"
if [[ -z "$replay_iso" && -f "$substrate_lib" ]]; then
  # shellcheck source=/dev/null
  source "$substrate_lib"
  replay_iso="$(substrate_resolve_iso_path "" 2>/dev/null || true)"
fi
if [[ -z "$replay_iso" ]]; then
  echo "ERROR: set COGOS_SUBSTRATE_ISO for pipeline replay source" >&2
  exit 5
fi

if [[ -f "$validate_substrate" ]]; then
  python3 "$validate_substrate" \
    --iso "$replay_iso" \
    --substrate-id "${COGOS_SUBSTRATE_ID:-auto}" \
    --registry "$registry" \
    --mode "${COGOS_SUBSTRATE_VALIDATION_MODE:-fail}" \
    --output "$output_dir/substrate-validation.json"
fi

validate_pipeline="${FORGE_ROOT}/scripts/build/validate-pipeline.py"
if [[ -f "$validate_pipeline" ]]; then
  python3 "$validate_pipeline" "$PIPELINE" --mode fail --output "$output_dir/pipeline-validation.json"
elif [[ -f "$REPO_ROOT/wolf-cog-os/scripts/validate-pipeline.py" ]]; then
  python3 "$REPO_ROOT/wolf-cog-os/scripts/validate-pipeline.py" "$PIPELINE" --mode fail --output "$output_dir/pipeline-validation.json"
fi

export COGOS_SUBSTRATE_ISO="$replay_iso"
export COGOS_BOOT_REPLAY_ISO="$replay_iso"
export COGOS_DEBIAN_ISO="$replay_iso"

forge_pipeline_maybe_build_rootfs "$COGOS_FORGE_PROFILE"

bash "$build_wrapper" --profile "$COGOS_FORGE_PROFILE" "$replay_iso"

BUILT_ISO="$COGOS_OUT"
if [[ ! -f "$BUILT_ISO" ]]; then
  BUILT_ISO="$(ls -1 "$output_dir"/*.iso 2>/dev/null | head -n 1 || true)"
fi

forge_pipeline_emit_lineage "$PIPELINE" "$output_dir" "$COGOS_FORGE_PROFILE"

if [[ -n "$BUILT_ISO" && -f "$BUILT_ISO" ]]; then
  forge_pipeline_emit_cloud_outputs "$BUILT_ISO" "$PIPELINE" "$output_dir/cloud"
fi

echo "Pipeline complete. Artifacts in: $output_dir"
