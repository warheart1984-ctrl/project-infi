#!/usr/bin/env python3
"""Alt-18 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT18_GENES = (
    "project_infi_state_machine_organ",
    "project_infi_law_organ",
    "run_ledger_binding_organ",
    "chat_turn_governance_organ",
    "aais_ul_substrate_organ",
    "aris_integration_organ",
    "governance_layer_organ",
    "security_protocol_organ",
    "system_guard_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT18_GENES
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
    alt18_ready = sum(
        1
        for gene in ALT18_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 93 and alt18_ready < 9:
        errors.append(
            f"expected at least 93 governed genomes before Alt-18 promotion (got {governed_count})"
        )
    if alt18_ready != 9:
        errors.append(f"expected 9 Alt-18 organs at mvp or governed (got {alt18_ready})")

    for gene in ALT18_GENES:
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
        "operator_cognition_coherence_fabric.v1.13"
    ):
        errors.append("coherence fabric must be v1.13")
    for key in (
        "law_cycle_posture",
        "turn_admission_posture",
        "governance_control_posture",
    ):
        if len(fabric.get(key) or []) != 3:
            errors.append(f"expected 3 {key} entries")
    for flag in (
        "law_cycle_aligned",
        "turn_admission_aligned",
        "governance_control_aligned",
        "project_infi_law_aligned",
    ):
        if not fabric.get(flag):
            errors.append(f"{flag} is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt18-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT18_GENES],
            "tests/test_operator_cognition_coherence_fabric.py",
            "tests/test_project_infi_law.py",
            "tests/test_chat_turn_governance.py",
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
        print("[alt18-governed-gate] FAIL: pytest")
        return 1
    print("[alt18-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
