#!/usr/bin/env python3
"""Alt-9 governed promotion eligibility — infrastructure organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT9_GENES = (
    "phase_gate_organ",
    "realtime_event_cause_predictor_organ",
    "invariant_engine_organ",
)

GOVERNED_PROOFS = {
    "phase_gate_organ": _ROOT / "docs/proof/platform/PHASE_GATE_ORGAN_GOVERNED_PROOF.md",
    "realtime_event_cause_predictor_organ": _ROOT
    / "docs/proof/platform/REALTIME_EVENT_CAUSE_PREDICTOR_ORGAN_GOVERNED_PROOF.md",
    "invariant_engine_organ": _ROOT
    / "docs/proof/platform/INVARIANT_ENGINE_ORGAN_GOVERNED_PROOF.md",
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT9_GENES:
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
    infra = fabric.get("infrastructure_posture") or []
    if len(infra) != 3:
        errors.append(f"expected 3 infrastructure_posture planes (got {len(infra)})")
    trace = {
        "realtime_event_cause_predictor": {
            "status": "bounded_inference",
            "runtime_context": "operator_runtime",
            "recommended_state": "observe",
            "cause_class": "steady_state",
            "advisory_only": True,
            "supporting_signals": [],
            "signal_count": 0,
            "phase_gate": {"decision": "ALLOW"},
        },
        "validation": {"realtime_event_cause_predictor_valid": True},
    }
    fabric_live = build_coherence_fabric_status(root=root, pipeline_trace=trace)
    if not fabric_live.get("infrastructure_substrate_aligned"):
        errors.append("infrastructure_substrate_aligned is false with live pipeline trace")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt9-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_phase_gate_organ.py",
            "tests/test_realtime_event_cause_predictor_organ.py",
            "tests/test_invariant_engine_organ.py",
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
        print("[alt9-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt9-governed-gate] PASS: Alt-9 infrastructure organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
