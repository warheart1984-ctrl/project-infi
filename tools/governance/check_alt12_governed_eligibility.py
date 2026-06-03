#!/usr/bin/env python3
"""Alt-12 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT12_GENES = (
    "otem_bounded_organ",
    "direct_challenge_organ",
    "orchestration_spine_organ",
    "operator_health_sentinel_organ",
    "governed_realtime_lane_organ",
    "v8_runtime_organ",
    "patch_apply_organ",
    "patch_execution_preview_organ",
    "run_ledger_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/platform/{gene.upper()}_GOVERNED_PROOF.md"
    for gene in ALT12_GENES
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT12_GENES:
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
        "operator_cognition_coherence_fabric.v1.7"
    ):
        errors.append("coherence fabric must be v1.7")
    if len(fabric.get("otem_lane_posture") or []) != 3:
        errors.append("expected 3 otem_lane_posture entries")
    if len(fabric.get("predictive_lane_posture") or []) != 3:
        errors.append("expected 3 predictive_lane_posture entries")
    if len(fabric.get("execution_depth_posture") or []) != 3:
        errors.append("expected 3 execution_depth_posture entries")

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
        "realtime_signal_feed": {"active_lane": "direct_cognitive"},
        "validation": {"realtime_event_cause_predictor_valid": True},
    }
    fabric_live = build_coherence_fabric_status(root=root, pipeline_trace=trace)
    if not fabric_live.get("otem_lane_aligned"):
        errors.append("otem_lane_aligned is false")
    if not fabric_live.get("predictive_lane_aligned"):
        errors.append("predictive_lane_aligned is false")
    if not fabric_live.get("execution_depth_aligned"):
        errors.append("execution_depth_aligned is false")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt12-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT12_GENES],
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
        print("[alt12-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt12-governed-gate] PASS: Alt-12 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
