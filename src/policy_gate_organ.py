"""Policy Gate Organ — documents blocked immune escalation; MP-X enrollment."""

# Mythic: Policy Gate Organ
# Engineering: PolicyGateGate
from __future__ import annotations

from typing import Any

from src.immune_policy_enrollment import STILL_BLOCKED, build_policy_enrollment_status

MODULE_ID = "AAIS-PG2-01"
ORGAN_VERSION = "policy_gate_organ.v1"


def build_policy_gate_status() -> dict[str, Any]:
    """Read-only escalation policy surface with enrolled predictor CLAMP/REROUTE."""
    enrollment = build_policy_enrollment_status()
    summary = (
        f"enrolled={len(enrollment.get('enrolled_escalations') or [])};"
        f"blocked={len(STILL_BLOCKED)};mpx_enrollment={enrollment.get('mpx_enrollment')}"
    )[:128]
    return {
        "policy_gate_organ_version": ORGAN_VERSION,
        "module_id": MODULE_ID,
        "status_summary": summary,
        "blocked_escalations": list(STILL_BLOCKED),
        "enrolled_escalations": list(enrollment.get("enrolled_escalations") or []),
        "mpx_enrollment": enrollment.get("mpx_enrollment"),
        "observe_protocol_only": False,
        "cisiv_stage": "implementation",
        "claim_label": "asserted",
        "read_only": True,
        "enrollment": enrollment,
    }
