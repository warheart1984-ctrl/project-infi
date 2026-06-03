#!/usr/bin/env python3
"""Release 20 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT20_GENES = (
    "memory_smith_organ",
    "operator_workspace_organ",
    "jarvis_runs_organ",
    "state_hygiene_organ",
    "blueprint_posture_organ",
    "workflow_interfaces_organ",
    "platform_console_interfaces_organ",
    "operator_console_interface_organ",
    "nova_workspace_interface_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT20_GENES
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
    alt20_ready = sum(
        1
        for gene in ALT20_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 111 and alt20_ready < 9:
        errors.append(
            f"expected at least 111 governed schemas before Release 20 promotion (got {governed_count})"
        )
    if alt20_ready != 9:
        errors.append(
            f"expected 9 Release 20 subsystems at mvp or governed (got {alt20_ready})"
        )

    for gene in ALT20_GENES:
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
        "operator_cognition_coherence_fabric.v1.15"
    ):
        errors.append("coherence layer must be v1.15")
    expected_lens = {
        "workspace_memory_layer": 3,
        "hygiene_blueprint_layer": 3,
        "extended_operator_interface_layer": 3,
    }
    for key, need in expected_lens.items():
        if len(fabric.get(key) or []) != need:
            errors.append(f"expected {need} {key} entries")
    for flag in (
        "workspace_memory_aligned",
        "hygiene_blueprint_aligned",
        "extended_operator_interface_aligned",
        "operator_workspace_interfaces_aligned",
    ):
        if not fabric.get(flag):
            errors.append(f"{flag} is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt20-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT20_GENES],
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
        print("[alt20-governed-gate] FAIL: pytest")
        return 1
    print("[alt20-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
