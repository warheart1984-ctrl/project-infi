#!/usr/bin/env bash
set -euo pipefail

output_emit() {
  echo "ERROR: cloud output vhd is registered but not implemented yet." >&2
  echo "       Contract: docs/forge-cloud-output-contract.md" >&2
  exit 4
}
