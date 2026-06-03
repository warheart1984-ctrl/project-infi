#!/usr/bin/env python3
"""Alt-10 governed promotion eligibility — nine organs at MVP."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

ALT10_GENES = (
    "verification_gate_organ",
    "memory_path_governance_organ",
    "knowledge_authority_organ",
    "scorpion_bridge_organ",
    "mechanic_handoff_organ",
    "forensic_triangulation_organ",
    "immune_observe_organ",
    "policy_gate_organ",
    "predictor_immune_bridge_organ",
)

GOVERNED_PROOFS = {
    gene: _ROOT / f"docs/proof/{subdir}/{gene.upper()}_GOVERNED_PROOF.md"
    for gene, subdir in (
        ("verification_gate_organ", "platform"),
        ("memory_path_governance_organ", "platform"),
        ("knowledge_authority_organ", "platform"),
        ("scorpion_bridge_organ", "forensics"),
        ("mechanic_handoff_organ", "forensics"),
        ("forensic_triangulation_organ", "forensics"),
        ("immune_observe_organ", "nova"),
        ("policy_gate_organ", "nova"),
        ("predictor_immune_bridge_organ", "nova"),
    )
}


def check_eligibility(root: Path | None = None) -> list[str]:
    root = root or _ROOT
    errors: list[str] = []

    from src.governance_organs.genome_engine import GenomeEngine
    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    GenomeEngine.reload(root)
    for gene in ALT10_GENES:
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
        "operator_cognition_coherence_fabric.v1.5"
    ):
        errors.append("coherence fabric must be v1.5")
    if len(fabric.get("memory_governance_posture") or []) != 3:
        errors.append("expected 3 memory_governance_posture entries")
    if len(fabric.get("forensics_posture") or []) != 3:
        errors.append("expected 3 forensics_posture entries")
    if len(fabric.get("immune_observe_posture") or []) != 3:
        errors.append("expected 3 immune_observe_posture entries")

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
    if not fabric_live.get("memory_paths_aligned"):
        errors.append("memory_paths_aligned is false")
    if not fabric_live.get("forensics_handoff_aligned"):
        errors.append("forensics_handoff_aligned is false")
    if not fabric_live.get("immune_observe_aligned"):
        errors.append("immune_observe_aligned is false with live pipeline trace")

    return errors


def main() -> int:
    errors = check_eligibility(_ROOT)
    if errors:
        for err in errors:
            print(f"[alt10-governed-gate] FAIL: {err}")
        return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT10_GENES],
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
        print("[alt10-governed-gate] FAIL: organ pytest")
        return 1
    print("[alt10-governed-gate] PASS: Alt-10 organs eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
