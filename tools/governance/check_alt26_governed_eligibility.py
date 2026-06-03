#!/usr/bin/env python3
"""Release 26 governed promotion eligibility."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT26_GENES = (
    "linguistic_governance_day_organ",
    "linguistic_work_order_history_organ",
    "linguistic_attestation_history_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT26_GENES
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    reg = GenomeEngine.registry()
    alt26_ready = sum(
        1
        for gene in ALT26_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if alt26_ready != 3:
        errors.append(
            f"expected 3 Release 26 subsystems at mvp or governed (got {alt26_ready})"
        )

    for gene in ALT26_GENES:
        data = reg.genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp before governed (got {stage})")
        proof_path = GOVERNED_PROOFS.get(gene)
        if proof_path and not proof_path.is_file():
            errors.append(f"missing governed proof: {proof_path.relative_to(root)}")

    fabric = build_coherence_fabric_status(root=root)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version not in {
        "operator_cognition_coherence_fabric.v1.22",
        "operator_cognition_coherence_fabric.v1.21",
        "operator_cognition_coherence_fabric.v1.20",
    }:
        errors.append(f"coherence layer must be v1.21+ (got {version})")
    if version in {
        "operator_cognition_coherence_fabric.v1.21",
        "operator_cognition_coherence_fabric.v1.22",
    }:
        if len(fabric.get("linguistic_operator_day_layer") or []) < 2:
            errors.append("expected 2 linguistic_operator_day_layer entries")
        if len(fabric.get("linguistic_retention_history_layer") or []) < 3:
            errors.append("expected 3 linguistic_retention_history_layer entries")
        if not fabric.get("linguistic_operational_closure_aligned"):
            errors.append("linguistic_operational_closure_aligned is false")

    closure = root / "docs/proof/platform/LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF.md"
    if not closure.is_file():
        errors.append("missing LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF.md")
    lifecycle = root / "docs/proof/platform/GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF.md"
    if not lifecycle.is_file():
        errors.append("missing GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF.md")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt26-governed-gate] FAIL: {err}")
        return 1
    print("[alt26-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
