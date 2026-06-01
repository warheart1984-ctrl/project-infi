#!/usr/bin/env bash
# Nightly Forge variant build orchestrator (P13).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT_DIR"

MATRIX="${COGOS_NIGHTLY_MATRIX:-wolf-cog-os/forge/nightly/variant-matrix.json}"
STAMP="${COGOS_NIGHTLY_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
OUT_ROOT="${COGOS_NIGHTLY_OUT:-ci-artifacts/nightly/${STAMP}}"
ISO_INPUT="${COGOS_SUBSTRATE_ISO:-${ISO:-Wolf-CoG-OS-full.iso}}"
BUILD_ISO="${COGOS_NIGHTLY_BUILD_ISO:-0}"

mkdir -p "$OUT_ROOT"

echo "=== Forge nightly variant build ==="
echo "matrix: $MATRIX"
echo "output: $OUT_ROOT"
echo "build_iso: $BUILD_ISO"

python3 - <<'PY' "$MATRIX" "$OUT_ROOT" "$BUILD_ISO" "$ISO_INPUT"
import json
import os
import subprocess
import sys
from pathlib import Path

matrix_path = Path(sys.argv[1])
out_root = Path(sys.argv[2])
build_iso = sys.argv[3] == "1"
iso_input = sys.argv[4]
repo = Path.cwd()

matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
variants = matrix.get("variants", [])
failures = []

for variant in variants:
    vid = variant["id"]
    pipeline = variant["pipeline"]
    profile = variant.get("profile", "forge-selfhosted")
    variant_dir = out_root / vid
    variant_dir.mkdir(parents=True, exist_ok=True)
    lineage_out = variant_dir / "forge-lineage.json"

    emit = subprocess.run(
        [
            sys.executable,
            "wolf-cog-os/scripts/emit-forge-lineage.py",
            "--pipeline",
            pipeline,
            "--profile",
            profile,
            "--output",
            str(lineage_out.relative_to(repo)),
        ],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if emit.returncode != 0:
        failures.append(f"{vid}: lineage emit failed")
        continue

    validate = subprocess.run(
        [
            sys.executable,
            "wolf-cog-os/scripts/validate-forge-lineage.py",
            "--lineage",
            str(lineage_out.relative_to(repo)),
            "--mode",
            "fail",
        ],
        cwd=str(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if validate.returncode != 0:
        failures.append(f"{vid}: lineage validate failed")

    if build_iso and Path(iso_input).is_file():
        iso_name = Path(pipeline).stem + ".iso"
        iso_out = variant_dir / iso_name
        print(f"[nightly-build] variant={vid} would build ISO from {iso_input}")
        subprocess.run(
            ["cp", iso_input, str(iso_out)],
            check=False,
        )
        if variant.get("emit_cloud"):
            script_dir = repo / "wolf-cog-os/scripts"
            subprocess.run(
                [
                    "bash",
                    str(script_dir / "lib/emit-pipeline-outputs.sh"),
                    str(iso_out),
                    pipeline,
                    str(variant_dir / "cloud"),
                ],
                cwd=str(repo),
                check=False,
            )
    elif build_iso and variant.get("required", False):
        failures.append(f"{vid}: required build but ISO input missing ({iso_input})")

summary = {
    "schema_version": "forge-nightly-build.v1",
    "stamp": out_root.name,
    "variants": [v["id"] for v in variants],
    "build_iso": build_iso,
    "iso_input": iso_input,
    "failures": failures,
    "status": "pass" if not failures else "fail",
}
(out_root / "nightly-build-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(f"nightly variant build: status={summary['status']} failures={len(failures)}")
for item in failures:
    print(f"[ERROR] {item}")
raise SystemExit(1 if failures else 0)
PY
