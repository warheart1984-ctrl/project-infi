#!/usr/bin/env bash
# Host-side Forge pipeline runner (repo paths; used by CI and local dev).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=paths.sh
source "$SCRIPT_DIR/paths.sh"
# shellcheck source=lib/forge-pipeline-run.sh
source "$SCRIPT_DIR/lib/forge-pipeline-run.sh"
# shellcheck source=lib/substrate-resolve.sh
source "$SCRIPT_DIR/lib/substrate-resolve.sh"

PIPELINE="${1:-${COGOS_FORGE_PIPELINE:-wolf-cog-os/forge/pipelines/daily-driver.yaml}}"
if [[ ! "$PIPELINE" = /* ]]; then
  PIPELINE="$REPO_ROOT/$PIPELINE"
fi

forge_pipeline_load_env "$PIPELINE"

OUTPUT_DIR="${COGOS_CI_ARTIFACT_DIR:-$REPO_ROOT/ci-artifacts/pipeline-runs/${COGOS_PIPELINE_NAME:-variant}}"
mkdir -p "$OUTPUT_DIR"
export COGOS_CI_ARTIFACT_DIR="$OUTPUT_DIR"

ISO_NAME="${COGOS_PIPELINE_ISO_NAME:-cogos-${COGOS_PIPELINE_NAME:-variant}.iso}"
export COGOS_OUT="${COGOS_OUT:-$WOLF_OUTPUT/$ISO_NAME}"
export COGOS_FORGE_PROFILE="${COGOS_FORGE_PROFILE:-forge-selfhosted}"
export COGOS_BOOT_PROFILE=forge
export COGOS_BUILD_FROM_TREE="${COGOS_BUILD_FROM_TREE:-1}"
export COGOS_GRUB_MERGE=1
export COGOS_ENABLE_PID1=0

REPLAY_ISO="${COGOS_SUBSTRATE_ISO:-${COGOS_BOOT_REPLAY_ISO:-$(substrate_resolve_iso_path "" 2>/dev/null || true)}}"
if [[ -z "$REPLAY_ISO" ]]; then
  REPLAY_ISO="${ISO:-${COGOS_DEBIAN_ISO:-$DEBIAN_BASE_ISO}}"
fi
if [[ ! -f "$REPLAY_ISO" ]]; then
  echo "ERROR: substrate ISO not found for pipeline run: ${REPLAY_ISO:-<unset>}" >&2
  exit 5
fi

substrate_export_env "$REPLAY_ISO"
export COGOS_SUBSTRATE_ISO="$REPLAY_ISO"
export COGOS_BOOT_REPLAY_ISO="$REPLAY_ISO"
export COGOS_DEBIAN_ISO="$REPLAY_ISO"

echo "=== Forge pipeline (host): ${COGOS_PIPELINE_NAME:-unknown} ==="
echo "Spec:      $PIPELINE"
echo "Backend:   ${COGOS_ROOTFS_BACKEND:-debootstrap}"
echo "Cloud:     ${COGOS_PIPELINE_CLOUD_FORMATS:-<none>}"
echo "Substrate: $REPLAY_ISO"
echo "Output:    $COGOS_OUT"
echo "Artifacts: $OUTPUT_DIR"

python3 "$SCRIPT_DIR/validate-substrate.py" \
  --iso "$REPLAY_ISO" \
  --substrate-id "${COGOS_SUBSTRATE_ID:-auto}" \
  --mode "${COGOS_SUBSTRATE_VALIDATION_MODE:-fail}" \
  --output "$OUTPUT_DIR/substrate-validation.json"

python3 "$SCRIPT_DIR/validate-pipeline.py" "$PIPELINE" --mode fail \
  --output "$OUTPUT_DIR/pipeline-validation.json"

forge_pipeline_maybe_build_rootfs "$COGOS_FORGE_PROFILE"

bash "$SCRIPT_DIR/build.sh" --profile "$COGOS_FORGE_PROFILE" "$REPLAY_ISO"

BUILT_ISO="$COGOS_OUT"
if [[ ! -f "$BUILT_ISO" ]]; then
  BUILT_ISO="$(ls -1 "$WOLF_OUTPUT"/*.iso 2>/dev/null | head -n 1 || true)"
fi

forge_pipeline_emit_lineage "$PIPELINE" "$OUTPUT_DIR" "$COGOS_FORGE_PROFILE"

if [[ -n "$BUILT_ISO" && -f "$BUILT_ISO" ]]; then
  cp -f "$BUILT_ISO" "$OUTPUT_DIR/" 2>/dev/null || true
  forge_pipeline_emit_cloud_outputs "$BUILT_ISO" "$PIPELINE" "$OUTPUT_DIR/cloud"
fi

echo "Pipeline complete. Artifacts in: $OUTPUT_DIR"
