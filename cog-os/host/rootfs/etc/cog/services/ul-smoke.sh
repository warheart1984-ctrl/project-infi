#!/bin/bash
# Offline AAIS-UL lineage smoke (forge-selfhosted payload_ul profiles).
set -euo pipefail

UL_ROOT=/opt/cogos/ul-tools
GRAPH="${COG_UL_LINEAGE_GRAPH:-$UL_ROOT/tools/ul/fixtures/lineage_multi_hop.json}"
MARK=/run/cog/ul.smoke.ok

if [[ ! -f "$GRAPH" ]]; then
  echo "ul-smoke: missing lineage graph $GRAPH" >&2
  exit 1
fi

export PYTHONPATH="$UL_ROOT"
cd "$UL_ROOT"
python3 -m tools.ul.smoke --lineage-graph "$GRAPH" --no-pytest >/run/cog/ul-smoke.log 2>&1
touch "$MARK"
echo "ul-smoke: ok -> $MARK"
