"""Governed immune policy enrollment (Release 33 immune closure)."""

# Mythic: Immune Policy Enrollment
# Engineering: ImmunePolicyEnrollmentEngine
from __future__ import annotations

from typing import Any

ENROLLED_ESCALATIONS = (
    "predictor_driven_clamp",
    "predictor_driven_reroute",
)

STILL_BLOCKED = (
    "autonomous_immune_coupling",
    "super_nova_live_execution",
    "predictor_driven_quarantine_without_mpx",
)


def build_policy_enrollment_status() -> dict[str, Any]:
    return {
        "mpx_enrollment": "enrolled",
        "enrolled_escalations": list(ENROLLED_ESCALATIONS),
        "blocked_escalations": list(STILL_BLOCKED),
        "observe_protocol_only": False,
        "predictor_clamp_min_confidence": 0.7,
        "predictor_reroute_min_severity": 0.8,
    }


def evaluate_predictor_bounded_escalation(
    *,
    confidence: float,
    severity: float,
    requested_response: str,
) -> dict[str, Any]:
    """Cap predictor-driven escalation at CLAMP/REROUTE; QUARANTINE remains blocked."""
    normalized = str(requested_response or "ALLOW").upper()
    status = build_policy_enrollment_status()
    if normalized == "QUARANTINE":
        return {
            "allowed": False,
            "response": "REJECT",
            "reason": "predictor_driven_quarantine_without_mpx",
            "enrollment": status,
        }
    if normalized == "CLAMP" and confidence >= float(status["predictor_clamp_min_confidence"]):
        return {"allowed": True, "response": "CLAMP", "enrollment": status}
    if normalized == "REROUTE" and severity >= float(status["predictor_reroute_min_severity"]):
        return {"allowed": True, "response": "REROUTE", "enrollment": status}
    return {"allowed": False, "response": "ALLOW", "reason": "below_threshold", "enrollment": status}


def record_predictor_escalation_incident(
    *,
    session_id: str,
    escalation: dict[str, Any],
) -> dict[str, Any] | None:
    incident = None
    try:
        from src.immune_system import immune_system

        incident = immune_system.observe_protocol_signal(
            {
                "code": "predictor_bounded_escalation",
                "message": str(escalation.get("reason") or escalation.get("response") or "predictor escalation"),
                "response": escalation.get("response"),
                "session_id": session_id,
            }
        )
    except Exception:
        incident = None
    try:
        from src.operator_decision_ledger import append_immune_escalation_event

        append_immune_escalation_event(session_id, escalation=escalation, incident=incident)
    except Exception:
        pass
    try:
        from src.operator_pager import maybe_page_immune_escalation

        maybe_page_immune_escalation(session_id, escalation)
    except Exception:
        pass
    return incident
