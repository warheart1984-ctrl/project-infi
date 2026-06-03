#!/usr/bin/env python3
"""Alt-19 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT19_GENES = (
    "launcher_organ",
    "aais_doctor_organ",
    "workflow_runtime_organ",
    "jarvis_console_surface_organ",
    "memory_bank_surface_organ",
    "dashboard_surface_organ",
    "nova_landing_surface_organ",
    "aais_composed_runtime_organ",
    "api_gateway_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT19_GENES
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
    alt19_ready = sum(
        1
        for gene in ALT19_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 102 and alt19_ready < 9:
        errors.append(
            f"expected at least 102 governed genomes before Alt-19 promotion (got {governed_count})"
        )
    if alt19_ready != 9:
        errors.append(f"expected 9 Alt-19 organs at mvp or governed (got {alt19_ready})")

    for gene in ALT19_GENES:
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
        "operator_cognition_coherence_fabric.v1.14"
    ):
        errors.append("coherence fabric must be v1.14")
    expected_lens = {
        "product_shell_posture": 3,
        "operator_surface_posture": 4,
        "composed_runtime_posture": 2,
    }
    for key, need in expected_lens.items():
        if len(fabric.get(key) or []) != need:
            errors.append(f"expected {need} {key} entries")
    for flag in (
        "product_shell_aligned",
        "operator_surface_aligned",
        "composed_runtime_aligned",
        "operator_product_shell_aligned",
    ):
        if not fabric.get(flag):
            errors.append(f"{flag} is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt19-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT19_GENES],
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
        print("[alt19-governed-gate] FAIL: pytest")
        return 1
    print("[alt19-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
