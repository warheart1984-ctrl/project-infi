#!/usr/bin/env python3
"""Alt-16 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT16_GENES = (
    "ai_factory_organ",
    "cogos_runtime_bridge_organ",
    "wolf_rehydration_organ",
    "forge_contractor_organ",
    "forge_eval_organ",
    "evolve_engine_organ",
    "slingshot_organ",
    "operator_workbench_organ",
    "workflow_shell_organ",
)

GOVERNED_PROOFS = {
    "ai_factory_organ": _ROOT / "docs/proof/ai_factory/AI_FACTORY_ORGAN_GOVERNED_PROOF.md",
}
for gene in ALT16_GENES:
    if gene not in GOVERNED_PROOFS:
        GOVERNED_PROOFS[gene] = (
            _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
        )


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
    alt16_ready = sum(
        1
        for gene in ALT16_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    alt16_governed = sum(
        1
        for gene in ALT16_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage") == "governed"
    )
    if governed_count < 75 and alt16_governed < 9:
        errors.append(
            f"expected at least 75 governed genomes before Alt-16 promotion (got {governed_count})"
        )
    if alt16_ready != 9:
        errors.append(f"expected 9 Alt-16 organs at mvp or governed (got {alt16_ready})")

    for gene in ALT16_GENES:
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
        "operator_cognition_coherence_fabric.v1.11"
    ):
        errors.append("coherence fabric must be v1.11")
    if len(fabric.get("factory_fabrication_posture") or []) != 3:
        errors.append("expected 3 factory_fabrication_posture entries")
    if len(fabric.get("contractor_lane_posture") or []) != 3:
        errors.append("expected 3 contractor_lane_posture entries")
    if len(fabric.get("kinetic_shell_posture") or []) != 3:
        errors.append("expected 3 kinetic_shell_posture entries")

    fabric_live = build_coherence_fabric_status(root=root)
    if not fabric_live.get("factory_fabrication_aligned"):
        errors.append("factory_fabrication_aligned is false")
    if not fabric_live.get("contractor_lanes_aligned"):
        errors.append("contractor_lanes_aligned is false")
    if not fabric_live.get("kinetic_shell_aligned"):
        errors.append("kinetic_shell_aligned is false")
    if not fabric_live.get("factory_kinetic_aligned"):
        errors.append("factory_kinetic_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt16-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT16_GENES],
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
        print("[alt16-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt16-governed-gate] PASS: Alt-16 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
