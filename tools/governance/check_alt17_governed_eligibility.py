#!/usr/bin/env python3
"""Alt-17 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT17_GENES = (
    "jarvis_protocol_organ",
    "reasoning_contract_organ",
    "jarvis_reasoning_lane_organ",
    "conversation_memory_organ",
    "continuity_substrate_organ",
    "jarvis_operator_organ",
    "anti_drift_organ",
    "prompt_assembly_organ",
    "output_integrity_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT17_GENES
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
    alt17_ready = sum(
        1
        for gene in ALT17_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    alt17_governed = sum(
        1
        for gene in ALT17_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage") == "governed"
    )
    if governed_count < 84 and alt17_governed < 9:
        errors.append(
            f"expected at least 84 governed genomes before Alt-17 promotion (got {governed_count})"
        )
    if alt17_ready != 9:
        errors.append(f"expected 9 Alt-17 organs at mvp or governed (got {alt17_ready})")

    for gene in ALT17_GENES:
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
        "operator_cognition_coherence_fabric.v1.12"
    ):
        errors.append("coherence fabric must be v1.12")
    if len(fabric.get("protocol_posture") or []) != 3:
        errors.append("expected 3 protocol_posture entries")
    if len(fabric.get("authority_shell_posture") or []) != 3:
        errors.append("expected 3 authority_shell_posture entries")
    if len(fabric.get("response_integrity_posture") or []) != 3:
        errors.append("expected 3 response_integrity_posture entries")

    if not fabric.get("protocol_aligned"):
        errors.append("protocol_aligned is false")
    if not fabric.get("authority_shell_aligned"):
        errors.append("authority_shell_aligned is false")
    if not fabric.get("response_integrity_aligned"):
        errors.append("response_integrity_aligned is false")
    if not fabric.get("authority_protocol_integrity_aligned"):
        errors.append("authority_protocol_integrity_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt17-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT17_GENES],
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
        print("[alt17-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt17-governed-gate] PASS: Alt-17 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
