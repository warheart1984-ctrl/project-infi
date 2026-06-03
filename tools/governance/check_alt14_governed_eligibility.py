#!/usr/bin/env python3
"""Alt-14 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT14_GENES = (
    "document_vision_organ",
    "ui_vision_organ",
    "perception_gateway_organ",
    "spatial_reasoning_organ",
    "mystic_engine_organ",
    "perception_lane_organ",
    "route_choice_organ",
    "specialist_route_organ",
    "provider_route_organ",
)

GOVERNED_PROOFS = {
    "document_vision_organ": _ROOT / "docs/proof/platform/DOCUMENT_VISION_ORGAN_GOVERNED_PROOF.md",
    "ui_vision_organ": _ROOT / "docs/proof/platform/UI_VISION_ORGAN_GOVERNED_PROOF.md",
    "perception_gateway_organ": _ROOT
    / "docs/proof/platform/PERCEPTION_GATEWAY_ORGAN_GOVERNED_PROOF.md",
    "spatial_reasoning_organ": _ROOT
    / "docs/proof/platform/SPATIAL_REASONING_ORGAN_GOVERNED_PROOF.md",
    "mystic_engine_organ": _ROOT / "docs/proof/platform/MYSTIC_ENGINE_ORGAN_GOVERNED_PROOF.md",
    "perception_lane_organ": _ROOT / "docs/proof/platform/PERCEPTION_LANE_ORGAN_GOVERNED_PROOF.md",
    "route_choice_organ": _ROOT / "docs/proof/platform/ROUTE_CHOICE_ORGAN_GOVERNED_PROOF.md",
    "specialist_route_organ": _ROOT
    / "docs/proof/platform/SPECIALIST_ROUTE_ORGAN_GOVERNED_PROOF.md",
    "provider_route_organ": _ROOT / "docs/proof/platform/PROVIDER_ROUTE_ORGAN_GOVERNED_PROOF.md",
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT14_GENES:
        data = GenomeEngine.registry().genomes.get(gene)
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
        "operator_cognition_coherence_fabric.v1.9"
    ):
        errors.append("coherence fabric must be v1.9")
    if len(fabric.get("perception_posture") or []) != 3:
        errors.append("expected 3 perception_posture entries")
    if len(fabric.get("spatial_symbolic_posture") or []) != 3:
        errors.append("expected 3 spatial_symbolic_posture entries")
    if len(fabric.get("route_choice_posture") or []) != 3:
        errors.append("expected 3 route_choice_posture entries")

    fabric_live = build_coherence_fabric_status(root=root)
    if not fabric_live.get("perception_aligned"):
        errors.append("perception_aligned is false")
    if not fabric_live.get("spatial_symbolic_aligned"):
        errors.append("spatial_symbolic_aligned is false")
    if not fabric_live.get("route_choice_aligned"):
        errors.append("route_choice_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt14-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT14_GENES],
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
        print("[alt14-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt14-governed-gate] PASS: Alt-14 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
