"""Mid-flight drift monitors for slingshot launch arc."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.formal.turn_agency import INTENT_DRIFT_EPSILON, measure_intent_shift
from src.stage2_fidelity_metrics import evaluate_stage2_fidelity


def evaluate_slingshot_midflight_cortex(
    session,
    *,
    packet: dict[str, Any],
    model_calls_this_turn: int = 0,
) -> dict[str, Any]:
    """Pre-reply monitors: cost ceiling and intent shift after cortex."""
    metadata = getattr(session, "metadata", None) or {}
    events: list[dict[str, Any]] = []
    halt_turn = False
    escalate = False
    signoff_required = False

    ceiling = int((packet.get("cost_envelope") or {}).get("max_model_calls_per_turn") or 3)
    if model_calls_this_turn > ceiling:
        events.append(
            {
                "monitor": "cost_ceiling",
                "code": "CST-07",
                "detail": f"model calls {model_calls_this_turn} exceed ceiling {ceiling}",
            }
        )
        halt_turn = True

    before = metadata.get("turn_boundary_before") or {}
    after_boundary = metadata.get("turn_boundary_after") or {}
    if before and after_boundary:
        delta = measure_intent_shift(
            before.get("intent"),
            after_boundary.get("intent"),
        )
        if delta > INTENT_DRIFT_EPSILON:
            events.append(
                {
                    "monitor": "intent_shift",
                    "code": "GOV-15",
                    "detail": f"intent shift delta {delta} exceeds epsilon",
                    "delta": delta,
                }
            )
            escalate = True
            signoff_required = True

    return {
        "phase": "cortex",
        "drift_events": events,
        "halt_turn": halt_turn,
        "escalate": escalate,
        "signoff_required": signoff_required,
        "impact_status": _impact_status(halt_turn, escalate, signoff_required),
    }


def evaluate_slingshot_midflight_reply(
    *,
    user_message: str,
    assistant_reply: str,
    packet: dict[str, Any],
    tool_invocations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Post-reply monitors: Stage 2 fidelity detectors."""
    report = evaluate_stage2_fidelity(
        user_message=user_message,
        assistant_reply=assistant_reply,
        authorized_goals=list(packet.get("authorized_goals") or []),
        required_constraints=list(packet.get("required_constraints") or []),
        tool_invocations=tool_invocations,
    )
    events = [
        {
            "monitor": "stage2_fidelity",
            "violation_class": item.violation_class,
            "detector_id": item.detector_id,
            "detail": item.detail,
            "evidence": item.evidence,
        }
        for item in report.violations
    ]
    halt_turn = any(item.violation_class == "III" for item in report.violations)
    escalate = bool(report.violations)
    signoff_required = any(item.violation_class in {"I", "II", "III"} for item in report.violations)
    return {
        "phase": "reply",
        "stage2_metrics": report.to_dict(),
        "drift_events": events,
        "halt_turn": halt_turn,
        "escalate": escalate,
        "signoff_required": signoff_required,
        "impact_status": _impact_status(halt_turn, escalate, signoff_required),
    }


def merge_midflight_reports(*reports: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    stage2_metrics: dict[str, Any] | None = None
    halt_turn = False
    escalate = False
    signoff_required = False
    for report in reports:
        events.extend(list(report.get("drift_events") or []))
        if report.get("stage2_metrics"):
            stage2_metrics = report["stage2_metrics"]
        halt_turn = halt_turn or bool(report.get("halt_turn"))
        escalate = escalate or bool(report.get("escalate"))
        signoff_required = signoff_required or bool(report.get("signoff_required"))
    merged = {
        "drift_events": events,
        "halt_turn": halt_turn,
        "escalate": escalate,
        "signoff_required": signoff_required,
        "impact_status": _impact_status(halt_turn, escalate, signoff_required),
    }
    if stage2_metrics:
        merged["stage2_metrics"] = stage2_metrics
    return merged


def apply_midflight_to_session(session, report: dict[str, Any]) -> None:
    """Persist escalation state on session metadata."""
    slingshot = dict((getattr(session, "metadata", None) or {}).get("slingshot") or {})
    if not slingshot.get("active"):
        return
    slingshot["last_midflight"] = report
    if report.get("escalate"):
        slingshot["status"] = "escalated"
        session.metadata["cortex_fast_path"] = False
        session.metadata["composed_turn_mode"] = "full"
    session.metadata["slingshot"] = slingshot


def _impact_status(halt_turn: bool, escalate: bool, signoff_required: bool) -> str:
    if halt_turn:
        return "halted"
    if signoff_required:
        return "signoff_required"
    if escalate:
        return "escalated"
    return "clean"
