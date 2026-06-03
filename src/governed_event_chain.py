"""Bounded governed event chain for realtime predictor -> invariants -> immune."""

# Mythic: Governed Event Chain Organ
# Engineering: GovernedEventChainEngine
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from typing import Any

from src.immune_system import ImmuneSystemController, immune_system
from src.invariant_engine import InvariantEngine
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    PhaseViolationError,
    assert_executable,
    get_component,
    is_executable,
    register_component,
)
from src.realtime_event_cause_predictor import (
    assert_valid_interpreted_event_state,
    interpret_realtime_signal_feed,
    validate_interpreted_event_state,
)


MODULE_ID = "aais.governed_event_chain"
MODULE_VERSION = "0.1"
CHAIN_COMPONENT_ID = "jarvis.governed_event_chain"
CHAIN_ALLOWED_CONTEXTS = ("live_runtime", "operator_runtime")
CHAIN_STATUS_PROCEED = "proceed"
CHAIN_STATUS_BLOCKED = "blocked"
CHAIN_DECISION_ALLOW = "ALLOW"
CHAIN_DECISION_BLOCK = "BLOCK"


def _normalize_runtime_context(value: Any) -> str:
    normalized = " ".join(str(value or "").split()).strip().lower()
    return normalized or "live_runtime"


def _normalize_event(event: dict[str, Any] | None, runtime_context: str) -> dict[str, Any]:
    payload = dict(event or {})
    payload["runtime_context"] = _normalize_runtime_context(
        payload.get("runtime_context") or runtime_context
    )
    signals = payload.get("signals")
    if not isinstance(signals, list):
        payload["signals"] = []
    payload["signal_count"] = int(payload.get("signal_count") or len(payload["signals"]))
    payload["validation"] = dict(payload.get("validation") or {})
    return payload


def _ensure_phase_component() -> None:
    try:
        get_component(CHAIN_COMPONENT_ID)
        return
    except ComponentNotRegisteredError:
        pass

    try:
        register_component(
            GovernedComponent(
                component_id=CHAIN_COMPONENT_ID,
                name="Governed Event Chain",
                component_type="governed_guardrail",
                phase=Phase.ACTIVE,
                allowed_contexts=list(CHAIN_ALLOWED_CONTEXTS),
                notes="Bounded runtime chain for predictor, invariant, and immune coordination.",
                validation_metadata={
                    "module_id": MODULE_ID,
                    "consumes": ["realtime_signal_feed", "realtime_event_cause_predictor"],
                    "advisory_only": True,
                },
            )
        )
    except PhaseGateError:
        pass


def _evaluate_phase_gate(runtime_context: str) -> dict[str, Any]:
    _ensure_phase_component()
    normalized_context = _normalize_runtime_context(runtime_context)
    try:
        component = get_component(CHAIN_COMPONENT_ID)
    except ComponentNotRegisteredError:
        component = None

    phase_state = {
        "component_id": CHAIN_COMPONENT_ID,
        "phase": component.phase.value if component else "unregistered",
        "allowed_contexts": list(component.allowed_contexts) if component else [],
        "runtime_context": normalized_context,
        "executable": is_executable(CHAIN_COMPONENT_ID, normalized_context) if component else False,
    }
    try:
        assert_executable(CHAIN_COMPONENT_ID, normalized_context)
    except PhaseViolationError as exc:
        return _wrap_ul_payload({
            "decision": CHAIN_DECISION_BLOCK,
            "reason": str(exc),
            "runtime_context": normalized_context,
            "component": phase_state,
        })
    return _wrap_ul_payload({
        "decision": CHAIN_DECISION_ALLOW,
        "reason": None,
        "runtime_context": normalized_context,
        "component": phase_state,
    })


def _severity_for_failed_invariants(failed_invariants: list[str]) -> str:
    high_impact = {
        "event_validation_pass",
        "prediction_validation_pass",
        "prediction_phase_allows",
        "runtime_context_match",
        "immune_alignment",
        "phase_gate_alignment",
    }
    if any(name in high_impact for name in failed_invariants):
        return "high"
    return "medium"


def _immune_reason(invariant_result: dict[str, Any]) -> str:
    failed = list(invariant_result.get("failed_invariants") or [])
    if not failed:
        return "Realtime governed event chain observed no invariant failures."
    return "Realtime invariant gate blocked prediction: " + ", ".join(failed)


def _handle_invariant_failure(
    *,
    event: dict[str, Any],
    prediction: dict[str, Any],
    invariant_result: dict[str, Any],
    immune_controller: ImmuneSystemController,
) -> dict[str, Any]:
    failed_invariants = list(invariant_result.get("failed_invariants") or [])
    return immune_controller.observe_protocol_signal(
        component_id=CHAIN_COMPONENT_ID,
        signal_type="realtime_invariant_violation",
        severity=_severity_for_failed_invariants(failed_invariants),
        reason=_immune_reason(invariant_result),
        details={
            "runtime_context": event.get("runtime_context"),
            "failed_invariants": failed_invariants,
            "reason_codes": list(invariant_result.get("reason_codes") or []),
            "event": event,
            "prediction": prediction,
            "invariant_result": invariant_result,
        },
    )


def governed_event(
    event: dict[str, Any] | None,
    *,
    prediction: dict[str, Any] | None = None,
    runtime_context: str | None = None,
    immune_controller: ImmuneSystemController | None = None,
) -> dict[str, Any]:
    """Run the bounded predictor -> invariant -> immune chain for one runtime event."""
    normalized_context = _normalize_runtime_context(runtime_context)
    event_payload = _normalize_event(event, normalized_context)
    phase_gate = _evaluate_phase_gate(event_payload["runtime_context"])
    controller = immune_controller or immune_system

    if phase_gate["decision"] == CHAIN_DECISION_BLOCK:
        invariant_result = {
            "module_id": "aais.invariant_engine.runtime_event_guard",
            "status": "fail",
            "allows": False,
            "checked_invariants": {"chain_phase_allows": False},
            "failed_invariants": ["chain_phase_allows"],
            "reason_codes": ["chain_phase_allows"],
            "summary": phase_gate["reason"],
            "advisory_only": True,
        }
        immune_action = controller.observe_protocol_signal(
            component_id=CHAIN_COMPONENT_ID,
            signal_type="governed_event_phase_block",
            severity="high",
            reason=str(phase_gate["reason"] or "Governed event chain phase gate blocked execution."),
            details={
                "runtime_context": event_payload["runtime_context"],
                "phase_gate": phase_gate,
                "event": event_payload,
            },
        )
        return _wrap_ul_payload({
            "module_id": MODULE_ID,
            "version": MODULE_VERSION,
            "runtime_context": event_payload["runtime_context"],
            "status": CHAIN_STATUS_BLOCKED,
            "decision": CHAIN_DECISION_BLOCK,
            "event": event_payload,
            "prediction": None,
            "invariant_result": invariant_result,
            "immune_action": immune_action,
            "phase_gate": phase_gate,
            "advisory_only": True,
        })

    prediction_payload = dict(
        prediction
        if prediction is not None
        else interpret_realtime_signal_feed(
            event_payload,
            runtime_context=event_payload["runtime_context"],
        )
    )
    assert_valid_interpreted_event_state(prediction_payload)
    invariant_result = InvariantEngine.validate_realtime_event_prediction(
        event_payload,
        prediction_payload,
    )

    immune_action = None
    decision = CHAIN_DECISION_ALLOW
    status = CHAIN_STATUS_PROCEED
    if not invariant_result["allows"]:
        immune_action = _handle_invariant_failure(
            event=event_payload,
            prediction=prediction_payload,
            invariant_result=invariant_result,
            immune_controller=controller,
        )
        decision = CHAIN_DECISION_BLOCK
        status = CHAIN_STATUS_BLOCKED

    return _wrap_ul_payload({
        "module_id": MODULE_ID,
        "version": MODULE_VERSION,
        "runtime_context": event_payload["runtime_context"],
        "status": status,
        "decision": decision,
        "event": event_payload,
        "prediction": prediction_payload,
        "invariant_result": invariant_result,
        "immune_action": immune_action,
        "phase_gate": phase_gate,
        "advisory_only": True,
    })


def validate_governed_event_result(result: dict[str, Any] | None) -> dict[str, bool]:
    """Return deterministic validation flags for one governed event chain result."""
    payload = dict(result or {})
    decision = payload.get("decision")
    prediction = payload.get("prediction")
    immune_action = payload.get("immune_action")
    return _wrap_ul_payload({
        "decision_known": decision in {CHAIN_DECISION_ALLOW, CHAIN_DECISION_BLOCK},
        "status_known": payload.get("status") in {CHAIN_STATUS_PROCEED, CHAIN_STATUS_BLOCKED},
        "event_present": isinstance(payload.get("event"), dict),
        "prediction_shape_valid": (
            prediction is None
            if decision == CHAIN_DECISION_BLOCK and "chain_phase_allows" in list(
                (payload.get("invariant_result") or {}).get("failed_invariants") or []
            )
            else isinstance(prediction, dict)
            and all(
                ok
                for ok in validate_interpreted_event_state(prediction).values()
                if isinstance(ok, bool)
            )
        ),
        "invariant_result_present": isinstance(payload.get("invariant_result"), dict)
        and isinstance((payload.get("invariant_result") or {}).get("allows"), bool),
        "immune_action_consistent": (
            immune_action is None if decision == CHAIN_DECISION_ALLOW else isinstance(immune_action, dict)
        ),
        "phase_gate_present": dict(payload.get("phase_gate") or {}).get("decision")
        in {CHAIN_DECISION_ALLOW, CHAIN_DECISION_BLOCK},
        "advisory_only_true": payload.get("advisory_only") is True,
        "runtime_context_explicit": bool(str(payload.get("runtime_context") or "").strip()),
    })
