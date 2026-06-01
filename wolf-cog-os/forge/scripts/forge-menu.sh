#!/usr/bin/env bash
# Forge Mode cockpit menu (runs inside the Forge ISO live environment).
set -euo pipefail

FORGE_ROOT="${FORGE_ROOT:-/forge}"
PIPELINE_DIR="${FORGE_ROOT}/pipelines"

if [[ ! -d "$PIPELINE_DIR" ]]; then
  echo "ERROR: Forge pipeline directory missing: $PIPELINE_DIR" >&2
  exit 2
fi

run_pipeline() {
  local spec="$1"
  if [[ ! -f "$spec" ]]; then
    echo "Pipeline not found: $spec" >&2
    return 1
  fi
  bash "${FORGE_ROOT}/scripts/forge-run-pipeline.sh" "$spec"
}

while true; do
  echo ""
  echo "=== Wolf CoG OS Forge Mode ==="
  echo "1) Build -> Minimal"
  echo "2) Build -> Daily Driver"
  echo "3) Build -> Recovery"
  echo "4) Build -> Custom (enter pipeline path)"
  echo "5) List pipelines"
  echo "q) Quit"
  read -r -p "Select: " choice

  case "${choice:-}" in
    1) run_pipeline "$PIPELINE_DIR/minimal.yaml" ;;
    2) run_pipeline "$PIPELINE_DIR/daily-driver.yaml" ;;
    3) run_pipeline "$PIPELINE_DIR/recovery.yaml" ;;
    4)
      read -r -p "Pipeline path: " custom
      run_pipeline "$custom"
      ;;
    5)
      ls -1 "$PIPELINE_DIR"/*.yaml 2>/dev/null || echo "(none)"
      ;;
    q|Q) exit 0 ;;
    *) echo "Unknown choice: $choice" ;;
  esac
done
