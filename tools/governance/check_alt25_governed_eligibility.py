#!/usr/bin/env python3
"""Release 25 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT25_GENES = (
    "linguistic_forecast_archive_organ",
    "linguistic_drift_report_organ",
    "linguistic_governance_work_order_organ",
    "linguistic_governance_cadence_organ",
    "linguistic_forecast_calibration_report_organ",
    "linguistic_full_governance_cycle_history_organ",
    "meta_linguistic_registry_organ",
    "linguistic_subsystem_promotion_organ",
    "linguistic_governed_lifecycle_fabric_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT25_GENES
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
    alt25_ready = sum(
        1
        for gene in ALT25_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 151 and alt25_ready < 9:
        errors.append(
            f"expected at least 151 governed schemas before Release 25 promotion "
            f"(got {governed_count})"
        )
    if alt25_ready != 9:
        errors.append(
            f"expected 9 Release 25 subsystems at mvp or governed (got {alt25_ready})"
        )

    for gene in ALT25_GENES:
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
    if fabric.get("operator_cognition_coherence_fabric_version") != (
        "operator_cognition_coherence_fabric.v1.20"
    ):
        errors.append("coherence layer must be v1.20")
    expected_lens = {
        "linguistic_operator_execution_layer": 3,
        "linguistic_lifecycle_artifact_layer": 4,
        "linguistic_promotion_layer": 1,
    }
    for key, need in expected_lens.items():
        if len(fabric.get(key) or []) != need:
            errors.append(f"expected {need} {key} entries")
    if not fabric.get("linguistic_governed_lifecycle_aligned"):
        errors.append("linguistic_governed_lifecycle_aligned is false")

    closure = root / "docs/proof/platform/GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF.md"
    if not closure.is_file():
        errors.append("missing GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF.md")
    attested = root / "docs/proof/platform/ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF.md"
    if not attested.is_file():
        errors.append("missing ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF.md")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt25-governed-gate] FAIL: {err}")
        return 1
    print("[alt25-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
