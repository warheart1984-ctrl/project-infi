#!/usr/bin/env python3
"""Release 21 governed promotion eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT21_GENES = (
    "creative_core_runtime_organ",
    "v9_core_organ",
    "v9_runtime_organ",
    "v10_core_organ",
    "v10_runtime_organ",
    "v10_action_engine_organ",
    "creative_capability_bridge_organ",
    "creative_operator_handoff_organ",
    "creative_console_interface_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT21_GENES
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
    alt21_ready = sum(
        1
        for gene in ALT21_GENES
        if (reg.genomes.get(gene) or {}).get("identity", {}).get("stage")
        in {"mvp", "governed"}
    )
    if governed_count < 120 and alt21_ready < 9:
        errors.append(
            f"expected at least 120 governed schemas before Release 21 promotion (got {governed_count})"
        )
    if alt21_ready != 9:
        errors.append(
            f"expected 9 Release 21 subsystems at mvp or governed (got {alt21_ready})"
        )

    for gene in ALT21_GENES:
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
        "operator_cognition_coherence_fabric.v1.16"
    ):
        errors.append("coherence layer must be v1.16")
    expected_lens = {
        "creative_core_layer": 3,
        "v9_creative_layer": 3,
        "v10_creative_layer": 3,
    }
    for key, need in expected_lens.items():
        if len(fabric.get(key) or []) != need:
            errors.append(f"expected {need} {key} entries")
    for flag in (
        "creative_core_aligned",
        "v9_creative_aligned",
        "v10_creative_aligned",
        "creative_runtime_v9_v10_aligned",
    ):
        if not fabric.get(flag):
            errors.append(f"{flag} is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt21-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT21_GENES],
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
        print("[alt21-governed-gate] FAIL: pytest")
        return 1
    print("[alt21-governed-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
