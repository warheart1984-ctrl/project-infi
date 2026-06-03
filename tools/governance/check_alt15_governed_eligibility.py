#!/usr/bin/env python3
"""Alt-15 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT15_GENES = (
    "reasoning_executive_organ",
    "attention_organ",
    "coherence_projection_organ",
    "deliberation_organ",
    "planning_organ",
    "cortex_arcs_organ",
    "cognitive_execution_organ",
    "speaking_runtime_organ",
    "nova_face_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/nova/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT15_GENES
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
    alt15_ready = sum(
        1
        for gene in ALT15_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    alt15_governed = sum(
        1
        for gene in ALT15_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage") == "governed"
    )
    if governed_count < 66 and alt15_governed < 9:
        errors.append(
            f"expected at least 66 governed genomes before Alt-15 promotion (got {governed_count})"
        )
    if alt15_ready != 9:
        errors.append(f"expected 9 Alt-15 organs at mvp or governed (got {alt15_ready})")

    for gene in ALT15_GENES:
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
    fabric_version = fabric.get("operator_cognition_coherence_fabric_version")
    if fabric_version not in (
        "operator_cognition_coherence_fabric.v1.10",
        "operator_cognition_coherence_fabric.v1.11",
    ):
        errors.append("coherence fabric must be v1.10 or v1.11")
    if len(fabric.get("executive_attention_posture") or []) != 3:
        errors.append("expected 3 executive_attention_posture entries")
    if len(fabric.get("deliberation_planning_posture") or []) != 3:
        errors.append("expected 3 deliberation_planning_posture entries")
    if len(fabric.get("voice_execution_posture") or []) != 3:
        errors.append("expected 3 voice_execution_posture entries")

    fabric_live = build_coherence_fabric_status(root=root)
    if not fabric_live.get("executive_attention_aligned"):
        errors.append("executive_attention_aligned is false")
    if not fabric_live.get("deliberation_planning_aligned"):
        errors.append("deliberation_planning_aligned is false")
    if not fabric_live.get("voice_execution_aligned"):
        errors.append("voice_execution_aligned is false")
    if not fabric_live.get("nova_lobe_voice_aligned"):
        errors.append("nova_lobe_voice_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt15-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT15_GENES],
            "tests/test_operator_cognition_coherence_fabric.py",
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
        print("[alt15-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt15-governed-gate] PASS: Alt-15 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
