#!/usr/bin/env bash
# QEMU qcow2 image from ISO (P14 production).
set -euo pipefail

output_emit() {
  local iso_path="$1"
  local output_path="${2:-${iso_path%.iso}.qcow2}"

  if [[ ! -f "$iso_path" ]]; then
    echo "ERROR: qcow2 input missing: $iso_path" >&2
    exit 4
  fi
  if ! command -v qemu-img >/dev/null 2>&1; then
    echo "ERROR: qemu-img required for qcow2 output" >&2
    exit 4
  fi

  mkdir -p "$(dirname "$output_path")"
  qemu-img convert -O qcow2 "$iso_path" "$output_path"
  echo "cloud output qcow2: $output_path"
}
