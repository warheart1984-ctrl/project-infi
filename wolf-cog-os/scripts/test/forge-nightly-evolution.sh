#!/usr/bin/env bash
# Forge platform evolution loop (P9 dry-run, P13 build mode).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

MODE="dry-run"
if [[ "${1:-}" == "--build" ]]; then
  MODE="build"
elif [[ "${1:-}" == "--dry-run" ]]; then
  MODE="dry-run"
fi

echo "=== Forge nightly evolution loop ==="
echo "mode: $MODE"

python3 wolf-cog-os/scripts/validate-pipeline.py --all --mode fail
python3 wolf-cog-os/scripts/validate-replay-adapter.py --mode fail
python3 .github/scripts/validate-substrate-evolution-ledger.py --mode fail
python3 .github/scripts/validate-backend-evolution-ledger.py --mode fail
python3 .github/scripts/validate-nightly-evolution-ledger.py --mode fail
python3 wolf-cog-os/scripts/validate-arch-matrix.py --mode fail
python3 wolf-cog-os/scripts/validate-cloud-output.py --format raw-img --registry-only --mode fail
python3 wolf-cog-os/scripts/validate-rootfs-backend.py --backend debootstrap --registry-only --mode fail
python3 wolf-cog-os/scripts/validate-rootfs-backend.py --backend pacstrap --registry-only --mode fail

python3 wolf-cog-os/scripts/emit-forge-lineage.py \
  --pipeline wolf-cog-os/forge/pipelines/daily-driver.yaml \
  --output ci-artifacts/nightly-forge-lineage.json
python3 wolf-cog-os/scripts/validate-forge-lineage.py \
  --lineage ci-artifacts/nightly-forge-lineage.json \
  --mode fail

python3 wolf-cog-os/scripts/emit-forge-lineage.py \
  --pipeline wolf-cog-os/forge/pipelines/daily-driver.yaml \
  --output ci-artifacts/nightly-forge-lineage-b.json \
  --build-host cross-machine-b
python3 wolf-cog-os/scripts/validate-lineage-reproducibility.py \
  --lineage-a ci-artifacts/nightly-forge-lineage.json \
  --lineage-b ci-artifacts/nightly-forge-lineage-b.json \
  --ignore-build-host \
  --mode fail

if [[ "$MODE" == "build" ]]; then
  export COGOS_NIGHTLY_BUILD_ISO=1
  bash wolf-cog-os/scripts/test/forge-nightly-build.sh
fi

echo "nightly evolution loop: pass"
