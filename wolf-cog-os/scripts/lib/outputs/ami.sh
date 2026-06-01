#!/usr/bin/env bash
set -euo pipefail

output_emit() {
  echo "ERROR: cloud output ami is registered but not implemented yet." >&2
  echo "       Contract: docs/forge-cloud-output-contract.md" >&2
  echo "       AMI bundle requires forge-lineage.json (requires_lineage=true)." >&2
  exit 4
}
