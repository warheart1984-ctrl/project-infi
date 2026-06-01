#!/usr/bin/env bash
# Cloud image output dispatcher (P8 contract stubs).
set -euo pipefail

emit_cloud_image() {
  local iso_path="$1"
  local format="${2:-${COGOS_CLOUD_OUTPUT_FORMAT:-raw-img}}"
  local output_path="${3:-}"
  local module="${SCRIPT_DIR:-}/lib/outputs/${format}.sh"

  if [[ ! -f "$module" ]]; then
    echo "ERROR: unknown cloud output format: $format" >&2
    echo "       See wolf-cog-os/forge/outputs/registry.json" >&2
    exit 3
  fi
  # shellcheck source=/dev/null
  source "$module"
  if ! declare -F output_emit >/dev/null 2>&1; then
    echo "ERROR: output module $format missing output_emit()" >&2
    exit 3
  fi
  output_emit "$iso_path" "$output_path"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  _dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  SCRIPT_DIR="$(cd "$_dir/.." && pwd)"
  emit_cloud_image "${1:-}" "${2:-}" "${3:-}"
fi
