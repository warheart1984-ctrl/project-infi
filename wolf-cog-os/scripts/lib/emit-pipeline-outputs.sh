#!/usr/bin/env bash
# Emit cloud outputs declared by a Forge pipeline spec (P14).
set -euo pipefail

emit_pipeline_outputs() {
  local iso_path="${1:?iso path required}"
  local pipeline="${2:-${COGOS_FORGE_PIPELINE:-wolf-cog-os/forge/pipelines/daily-driver.yaml}}"
  local out_dir="${3:-${COGOS_CI_ARTIFACT_DIR:-ci-artifacts}/pipeline-outputs}"

  if [[ ! -f "$iso_path" ]]; then
    echo "ERROR: ISO not found for pipeline outputs: $iso_path" >&2
    return 4
  fi

  mkdir -p "$out_dir"
  local formats
  formats="$(python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, "${SCRIPT_DIR}/lib")
from forge_pipeline import nested_get, parse_simple_yaml
spec = parse_simple_yaml(Path("${pipeline}"))
output = spec.get("output", {})
formats = output.get("cloud_formats", []) if isinstance(output, dict) else []
for fmt in formats:
    print(fmt)
PY
)"

  if [[ -z "$formats" ]]; then
    echo "pipeline outputs: no cloud_formats declared in $pipeline"
    return 0
  fi

  local fmt base
  base="$(basename "$iso_path" .iso)"
  while IFS= read -r fmt; do
    [[ -n "$fmt" ]] || continue
    local dest="$out_dir/${base}.${fmt}"
    case "$fmt" in
      raw-img) dest="$out_dir/${base}.img" ;;
      qcow2) dest="$out_dir/${base}.qcow2" ;;
      vhd) dest="$out_dir/${base}.vhd" ;;
      ami) dest="$out_dir/${base}.ami.json" ;;
    esac
    echo "[pipeline-output] emitting $fmt -> $dest"
    emit_cloud_image "$iso_path" "$fmt" "$dest"
  done <<< "$formats"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SCRIPT_DIR="$(cd "$_dir/.." && pwd)"
  # shellcheck source=emit-cloud-image.sh
  source "$SCRIPT_DIR/lib/emit-cloud-image.sh"
  emit_pipeline_outputs "${1:-}" "${2:-}" "${3:-}"
fi
