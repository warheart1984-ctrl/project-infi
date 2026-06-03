#!/usr/bin/env python3
"""Alt-8 governed promotion eligibility — mind-plane organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT8_GENES = (
    "continuity_witness_organ",
    "narrative_continuity_organ",
    "intent_agency_organ",
)

GOVERNED_PROOFS = {
    "continuity_witness_organ": _ROOT
    / "docs/proof/cognitive_runtime/CONTINUITY_WITNESS_ORGAN_GOVERNED_PROOF.md",
    "narrative_continuity_organ": _ROOT
    / "docs/proof/cognitive_runtime/NARRATIVE_CONTINUITY_ORGAN_GOVERNED_PROOF.md",
    "intent_agency_organ": _ROOT
    / "docs/proof/cognitive_runtime/INTENT_AGENCY_ORGAN_GOVERNED_PROOF.md",
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT8_GENES:
        data = GenomeEngine.registry().genomes.get(gene)
        if not data:
            errors.append(f"missing genome: {gene}")
            continue
        stage = (data.get("identity") or {}).get("stage", "")
        if stage not in {"mvp", "governed"}:
            errors.append(f"{gene} must be mvp before governed promotion (got {stage})")
        surface = (data.get("runtime") or {}).get("surface") or []
        if not surface:
            errors.append(f"{gene} missing runtime.surface")
        proof_path = GOVERNED_PROOFS.get(gene)
        if proof_path and not proof_path.is_file():
            errors.append(f"missing governed proof: {proof_path.relative_to(root)}")

    fabric = build_coherence_fabric_status(root=root)
    if not fabric.get("fabric_genes_aligned"):
        errors.append("coherence fabric not aligned")
    mind_posture = fabric.get("mind_posture") or []
    if len(mind_posture) != 3:
        errors.append(f"expected 3 mind_posture planes (got {len(mind_posture)})")
    if not fabric.get("mind_planes_aligned"):
        errors.append("mind_planes_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt8-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_continuity_witness_organ.py", "tests/test_narrative_continuity_organ.py", "tests/test_intent_agency_organ.py", "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        print("[alt8-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt8-governed-gate] PASS: Alt-8 mind-plane organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
