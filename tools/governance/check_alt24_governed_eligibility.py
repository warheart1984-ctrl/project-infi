#!/usr/bin/env python3
"""Release 24 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT24_GENES = (
    "linguistic_forecast_calibration_organ",
    "linguistic_governance_queue_organ",
    "linguistic_full_governance_cycle_organ",
    "linguistic_governance_attestation_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT24_GENES
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    governed_count = sum(
        1
        for data in reg.genomes.values()
        if (data.get("identity") or {}).get("stage") == "governed"
    )
    alt24_ready = sum(
        1
        for gene in ALT24_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 147 and alt24_ready < 4:
        errors.append(
            f"expected at least 147 governed schemas before Release 24 promotion "
            f"(got {governed_count})"
        )
    if alt24_ready != 4:
        errors.append(
            f"expected 4 Release 24 subsystems at mvp or governed (got {alt24_ready})"
        )

    for gene in ALT24_GENES:
        data = reg.genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp before governed (got {stage})")
        surface = (data.get("runtime") or {}).get("surface") or []
        if not surface:
            errors.append(f"{gene} missing runtime.surface")
        proof_path = GOVERNED_PROOFS.get(gene)
        if proof_path and not proof_path.is_file():
            errors.append(f"missing governed proof: {proof_path.relative_to(root)}")

    fabric = build_coherence_fabric_status(root=root)
    fabric_ver = fabric.get("operator_cognition_coherence_fabric_version")
    if fabric_ver not in (
        "operator_cognition_coherence_fabric.v1.19",
        "operator_cognition_coherence_fabric.v1.20",
    ):
        errors.append("coherence layer must be v1.19 or v1.20")
    expected_lens = {
        "linguistic_calibration_layer": 3,
        "linguistic_governance_queue_layer": 3,
        "linguistic_attestation_layer": 3,
    }
    for key, need in expected_lens.items():
        if len(fabric.get(key) or []) != need:
            errors.append(f"expected {need} {key} entries")
    if not fabric.get("linguistic_attested_closed_loop_aligned"):
        errors.append("linguistic_attested_closed_loop_aligned is false")

    closure = root / "docs/proof/platform/ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF.md"
    if not closure.is_file():
        errors.append("missing ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF.md")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt24-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT24_GENES],
            "tests/test_operator_cognition_coherence_fabric.py::test_alt24_attested_closed_loop_layers_at_v119",
            "-q",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[alt24-governed-gate] FAIL: pytest")
        return 1
    print("[alt24-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
