"""Verification Gate Organ — read-only mission verification gate snapshot."""

# Mythic: Verification Gate Organ
# Engineering: VerificationGateGate
from __future__ import annotations

from typing import Any

from src.verification_gate import GateDecision, evaluate_verification_gate

MODULE_ID = "AAIS-VG-01"
ORGAN_VERSION = "verification_gate_organ.v1"


def build_verification_gate_status(
    *,
    pending_test_count: int = 0,
    last_decision: str | None = None,
) -> dict[str, Any]:
    """Bounded verification gate posture for governance and coherence join."""
    evaluation = evaluate_verification_gate([])
    decision = str(last_decision or evaluation.decision.value or GateDecision.ELIGIBLE.value)
    summary = (
        f"decision={decision};pending_tests={max(0, int(pending_test_count or 0))};"
        f"reasons={len(evaluation.reasons)}"
    )[:128]
    return {
        "verification_gate_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "gate_decision": decision,
        "pending_test_count": max(0, int(pending_test_count or 0)),
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
    }
