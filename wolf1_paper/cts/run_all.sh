#!/usr/bin/env bash
# Constitutional Test Suite Runner (CTS)
# Runs all governance checks before any document is allowed to build.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== [CTS] Constitutional Test Suite ==="

GOV_REG="registries/governance.yaml"
REQ_REG="registries/requirements.yaml"
ART_REG="registries/artifacts.yaml"
ADR_DIR="adr"
SPEC_DIR="specifications"
VERSION_FILE=".governance/version.yaml"

if ! command -v yq >/dev/null 2>&1; then
  echo "[CTS] yq not found — falling back to node cts/run_all.mjs"
  exec node cts/run_all.mjs
fi

# 0. Version manifest
echo "[CTS] Validating version manifest..."
yq eval '.' "$VERSION_FILE" > /dev/null

# 1. Validate registry YAML syntax
echo "[CTS] Validating registry YAML files..."
yq eval '.' "$GOV_REG" > /dev/null
yq eval '.' "$REQ_REG" > /dev/null
yq eval '.' "$ART_REG" > /dev/null

# 2. Validate ADRs exist and have required fields
echo "[CTS] Validating ADR structure..."
shopt -s nullglob
adrs=("$ADR_DIR"/ADR-*.md)
if [ ${#adrs[@]} -eq 0 ]; then
  echo "[CTS][FAIL] No ADR files in $ADR_DIR"
  exit 1
fi
for adr in "${adrs[@]}"; do
  if ! grep -q "## Context" "$adr"; then
    echo "[CTS][FAIL] ADR missing Context: $adr"
    exit 1
  fi
  if ! grep -q "## Decision" "$adr"; then
    echo "[CTS][FAIL] ADR missing Decision: $adr"
    exit 1
  fi
  if ! grep -q "## Evidence" "$adr"; then
    echo "[CTS][FAIL] ADR missing Evidence: $adr"
    exit 1
  fi
done

# 3. Validate Requirements Registry links to real ADRs
echo "[CTS] Validating requirement → ADR traceability..."
ADR_IDS=$(ls "$ADR_DIR"/ADR-*.md 2>/dev/null | xargs -n1 basename | sed 's/.md$//')

while IFS= read -r req_adr; do
  [ -z "$req_adr" ] && continue
  [ "$req_adr" = "null" ] && continue
  if ! echo "$ADR_IDS" | grep -qx "$req_adr"; then
    echo "[CTS][FAIL] Requirement references missing ADR: $req_adr"
    exit 1
  fi
done < <(yq '.requirements[].traceability[].adr_id' "$REQ_REG")

# 4. Validate Artifact Registry references
echo "[CTS] Validating artifact registry integrity..."
while IFS= read -r art; do
  if [ -z "$art" ] || [ "$art" = "null" ]; then
    echo "[CTS][FAIL] Empty artifact ID"
    exit 1
  fi
done < <(yq '.artifacts[].id' "$ART_REG")

# 5. Validate constitutional amendment flow
echo "[CTS] Checking amendment ordering..."
shopt -s nullglob
amend_files=(amendments/amendment-*.md)
AMEND_COUNT=${#amend_files[@]}
if [ "$AMEND_COUNT" -eq 0 ]; then
  echo "[CTS][WARN] No amendment files found"
else
  for i in $(seq 1 "$AMEND_COUNT"); do
    expected=$(printf "amendment-%04d.md" "$i")
    if [ ! -f "amendments/$expected" ]; then
      echo "[CTS][FAIL] Missing amendment: $expected"
      exit 1
    fi
  done
fi

# 6. Validate specs exist for core requirements
echo "[CTS] Validating specification references..."
while IFS= read -r spec; do
  [ -z "$spec" ] && continue
  [ "$spec" = "null" ] && continue
  spec_base=$(basename "$spec")
  if [ ! -f "$SPEC_DIR/$spec_base" ] && [ ! -f "$spec" ]; then
    echo "[CTS][FAIL] Missing specification: $spec (looked in $SPEC_DIR/$spec_base)"
    exit 1
  fi
done < <(yq '.requirements[].specification' "$REQ_REG")

# 7. Wolf-1 document source exists
echo "[CTS] Validating governed document source..."
SRC=$(yq ".documents[] | select(.id==\"wolf1-arch\") | .source" "$VERSION_FILE")
if [ ! -f "$SRC" ]; then
  echo "[CTS][FAIL] Missing source: $SRC"
  exit 1
fi

# 8. Traceability chain validation
echo "[CTS] Validating traceability chains..."
if command -v python3 >/dev/null 2>&1; then
  python3 scripts/validate_traceability_chain.py
elif command -v python >/dev/null 2>&1; then
  python scripts/validate_traceability_chain.py
else
  echo "[CTS][WARN] Python not found — skipping traceability validator"
fi

echo "=== [CTS] All governance checks passed ==="
