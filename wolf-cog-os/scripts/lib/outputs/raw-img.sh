#!/usr/bin/env bash
# Raw block image from ISO (P14 production).
set -euo pipefail

output_emit() {
  local iso_path="$1"
  local output_path="${2:-${iso_path%.iso}.img}"

  if [[ ! -f "$iso_path" ]]; then
    echo "ERROR: raw-img input missing: $iso_path" >&2
    exit 4
  fi

  mkdir -p "$(dirname "$output_path")"
  if command -v dd >/dev/null 2>&1; then
    dd if="$iso_path" of="$output_path" bs=4M status=none conv=sparse
  else
    cp "$iso_path" "$output_path"
  fi
  echo "cloud output raw-img: $output_path ($(stat -c%s "$output_path" 2>/dev/null || wc -c <"$output_path") bytes)"
}
