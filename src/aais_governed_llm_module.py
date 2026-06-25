"""Proposal-only governed LLM seam behind the Cognitive Bridge.

This module does not invoke providers directly. It turns bridge-cleared
generation and deliberation packets into one bounded provider proposal envelope
that downstream runtime layers may inspect, trace, and choose to honor.
"""

# Mythic: Aais Governed Llm Module
# Engineering: AaisGovernedLlmModuleEngine
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from src.model_routing import resolve_model_route
from src.module_governance import ModuleGovernanceController, module_governance
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseViolationError,
    assert_executable,
    assert_routable,
    get_component,
    register_component,
)
from src.provider_registry import ProviderRegistry, provider_registry
from src.verification_gate import (
    INTENT_MISS,
    LAW_BREAK,
    VerificationTestResult,
    evaluate_verification_gate,
)


GOVERNED_LLM_MODULE_ID = "aais.governed_llm_module"
GOVERNED_LLM_MODULE_VERSION = "0.1"
GOVERNED_LLM_ALLOWED_CONTEXTS = [
    "live_runtime",
    "operator_runtime",
    "test_harness",
]
GOVERNED_LLM_ALLOWED_PACKET_TYPES = {
    "generation_request",
    "deliberation_request",
}
GOVERNED_LLM_ALLOWED_OUTPUT_SHAPE = [
    "module_id",
    "version",
    "status",
    "reason",
    "proposal_only",
    "execution_authority",
    "mutation_authority",
    "bounded_envelope",
    "runtime_context",
    "bridge_decision",
    "packet_type",
    "requested_provider",
    "requested_provider_mode",
    "provider_resolution",
    "provider_request",
    "phase_gate",
    "module_governance",
    "verification_gate",
    "declared_transitions",
    "notes",
    "trace",
]
GOVERNED_LLM_DECLARED_TRANSITIONS = [
    "bridge_received",
    "phase_gate_checked",
    "module_governance_checked",
    "provider_route_proposed",
    "verification_evaluated",
    "proposal_committed_or_blocked",
]


def _clean_text(value: Any, *, default: str = "") -> str:
    return " ".join(str(value or "").split()).strip() or default


def _normalize_name(value: Any, *, default: str = "") -> str:
    return _clean_text(value, default=default).lower().replace("-", "_").replace(" ", "_")


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _normalize_runtime_context(value: Any) -> str:
    normalized = _normalize_name(value, default="live_runtime")
    return normalized or "live_runtime"


def _derive_requested_provider(payload: dict[str, Any], explicit_provider: str | None) -> str | None:
    normalized_provider = _normalize_name(
        explicit_provider
        or payload.get("provider")
        or payload.get("provider_id")
        or payload.get("requested_provider"),
    )
    return normalized_provider or None


def _derive_requested_provider_mode(
    payload: dict[str, Any],
    explicit_provider_mode: str | None,
) -> str | None:
    normalized_mode = _normalize_name(explicit_provider_mode or payload.get("provider_mode"))
    return normalized_mode or None


def _provider_from_mode(provider_mode: str | None) -> str | None:
    mapping = {
        "claude_first": "claude",
        "openrouter_first": "openrouter",
        "local_first": "local",
    }
    return mapping.get(_normalize_name(provider_mode))


def _default_response_mode(packet_type: str, payload: dict[str, Any]) -> str:
    explicit = _normalize_name(payload.get("response_mode"))
    if explicit:
        return explicit
    if packet_type == "deliberation_request":
        return "think"
    return "fast"


def _ensure_phase_component_registered() -> GovernedComponent:
    try:
        return get_component(GOVERNED_LLM_MODULE_ID)
    except ComponentNotRegisteredError:
        register_component(
            GovernedComponent(
                component_id=GOVERNED_LLM_MODULE_ID,
                name="AAIS Governed LLM Seam",
                component_type="governed_llm_seam",
                phase=Phase.ACTIVE,
                allowed_contexts=list(GOVERNED_LLM_ALLOWED_CONTEXTS),
                notes=(
                    "Proposal-only provider-routing seam behind the Cognitive Bridge. "
                    "It emits bounded provider requests and never invokes providers directly."
                ),
            )
        )
        return get_component(GOVERNED_LLM_MODULE_ID)


def _phase_gate_status(runtime_context: str) -> dict[str, Any]:
    _ensure_phase_component_registered()
    normalized_context = _normalize_runtime_context(runtime_context)
    try:
        assert_routable(GOVERNED_LLM_MODULE_ID, normalized_context)
        assert_executable(GOVERNED_LLM_MODULE_ID, normalized_context)
    except PhaseViolationError as exc:
        return {
            "decision": "BLOCK",
            "component_id": GOVERNED_LLM_MODULE_ID,
            "runtime_context": normalized_context,
            "reason": str(exc),
        }
    return {
        "decision": "ALLOW",
        "component_id": GOVERNED_LLM_MODULE_ID,
        "runtime_context": normalized_context,
        "reason": "Governed LLM seam is admitted in this runtime context.",
    }


def build_governed_llm_module_spec(
    module_id: str = GOVERNED_LLM_MODULE_ID,
) -> dict[str, Any]:
    """Return the module-governance contract for the governed LLM seam."""
    return {
        "module_id": module_id,
        "label": "AAIS Governed LLM Seam",
        "lane": "governed_llm_seam",
        "declared_scope": [
            "cognitive_bridge",
            "model_routing",
            "provider_registry",
            "verification_gate",
            "governed_trace",
        ],
        "declared_surfaces": list(GOVERNED_LLM_ALLOWED_CONTEXTS),
        "capabilities": [
            "proposal_only_provider_resolution",
            "bounded_provider_request_envelope",
            "bridge_bound_llm_routing",
            "trace_ready_route_proposal",
        ],
        "cisiv": {
            "concept": {
                "status": "passed",
                "summary": "Provider routing must sit behind the bridge instead of creating a parallel execution seam.",
            },
            "identity": {
                "status": "passed",
                "summary": "The seam is proposal-only and keeps authority local to AAIS runtime governance.",
            },
            "structure": {
                "status": "passed",
                "summary": "Only generation and deliberation packets may enter, and all outputs remain bounded and declared.",
            },
            "implementation": {
                "status": "implemented",
                "summary": "The module emits governed provider proposals without invoking providers directly.",
            },
            "verification": {
                "status": "verified",
                "summary": "Coverage proves the seam blocks unsupported packets, honors bridge law, and emits bounded trace-ready proposals.",
                "evidence": [
                    "pytest tests/test_aais_governed_llm_module.py -q",
                    "pytest tests/test_cognitive_bridge.py -q",
                ],
            },
        },
        "compliance": {
            "stores_persistent_user_metadata": False,
            "creates_user_identity_profiles": False,
            "retains_behavioral_history": False,
            "infers_user_labels": False,
            "builds_personality_models": False,
            "builds_behavior_models": False,
            "stores_live_signals": False,
            "reconstructs_signals": False,
            "requires_identity_history": False,
            "adaptive_logic_scope": "system",
            "alters_nova_tone": False,
            "alters_nova_role": False,
            "alters_nova_constancy": False,
            "bypasses_jarvis_authority": False,
            "bypasses_routing": False,
            "logs_user_identity": False,
            "logs_behavior_patterns": False,
            "logs_biometric_traces": False,
            "hidden_logging": False,
            "exfiltrates_data": False,
        },
    }


def _module_governance_status(
    controller: ModuleGovernanceController | None,
) -> dict[str, Any]:
    active_controller = controller or module_governance
    module_record = active_controller.get_module(GOVERNED_LLM_MODULE_ID)
    if module_record is None:
        module_record = active_controller.admit_module(
            build_governed_llm_module_spec(),
            actor_id="cognitive_bridge",
            actor_role="system",
        )["module"]
    runtime_posture = dict(module_record.get("runtime_posture") or {})
    allowed = bool(
        module_record.get("status") == "admitted"
        and runtime_posture.get("routing_access")
    )
    return {
        "decision": "ALLOW" if allowed else "BLOCK",
        "module_id": GOVERNED_LLM_MODULE_ID,
        "status": module_record.get("status"),
        "lane": module_record.get("lane"),
        "runtime_posture": runtime_posture,
        "summary": module_record.get("admission_summary"),
    }


def _build_verification_gate(
    *,
    bridge_decision: str,
    packet_type: str,
    execution_intent: str,
) -> dict[str, Any]:
    tags: set[str] = set()
    law_score = 3
    intent_score = 3
    if bridge_decision == "BLOCK":
        tags.add(LAW_BREAK)
        law_score = 0
    if packet_type not in GOVERNED_LLM_ALLOWED_PACKET_TYPES or execution_intent == "execute":
        tags.add(INTENT_MISS)
        intent_score = 0
    evaluation = evaluate_verification_gate(
        [
            VerificationTestResult(
                test_id="governed_llm_boundary",
                law=law_score,
                intent=intent_score,
                role=3,
                constraint=3,
                drift=3,
                tags=tags,
            )
        ]
    )
    return {
        "decision": evaluation.decision.value,
        "reasons": list(evaluation.reasons),
        "failed_tests": list(evaluation.failed_tests),
    }


def _blocked_envelope(
    *,
    bridge_result: dict[str, Any],
    runtime_context: str,
    bridge_decision: str,
    packet_type: str,
    requested_provider: str | None,
    requested_provider_mode: str | None,
    reason: str,
    notes: list[str] | None,
    phase_gate: dict[str, Any],
    module_governance_gate: dict[str, Any],
    verification_gate: dict[str, Any],
) -> dict[str, Any]:
    trace = [
        {"stage": "bridge_received", "value": bridge_decision},
        {"stage": "phase_gate", "value": dict(phase_gate)},
        {"stage": "module_governance", "value": dict(module_governance_gate)},
        {"stage": "verification_gate", "value": dict(verification_gate)},
        {"stage": "proposal_commit", "value": "BLOCK"},
    ]
    return {
        "module_id": GOVERNED_LLM_MODULE_ID,
        "version": GOVERNED_LLM_MODULE_VERSION,
        "status": "BLOCKED",
        "reason": reason,
        "proposal_only": True,
        "execution_authority": "none",
        "mutation_authority": "none",
        "bounded_envelope": True,
        "runtime_context": runtime_context,
        "bridge_decision": bridge_decision,
        "packet_type": packet_type,
        "requested_provider": requested_provider,
        "requested_provider_mode": requested_provider_mode,
        "provider_resolution": None,
        "provider_request": None,
        "phase_gate": phase_gate,
        "module_governance": module_governance_gate,
        "verification_gate": verification_gate,
        "allowed_output_shape": list(GOVERNED_LLM_ALLOWED_OUTPUT_SHAPE),
        "declared_transitions": list(GOVERNED_LLM_DECLARED_TRANSITIONS),
        "notes": list(notes or []),
        "trace": trace,
        "bridge_result_fingerprint": _fingerprint(bridge_result),
    }


def propose_governed_llm_envelope(
    bridge_result: dict[str, Any] | None,
    *,
    requested_provider: str | None = None,
    requested_provider_mode: str | None = None,
    provider_registry_instance: ProviderRegistry | None = None,
    module_governance_controller: ModuleGovernanceController | None = None,
) -> dict[str, Any]:
    """Build a bounded provider proposal from a bridge-cleared LLM packet."""
    payload = dict(bridge_result or {})
    normalized_input = dict(payload.get("normalized_input") or {})
    governance_packet = dict(payload.get("governance_packet") or {})
    input_payload = dict(normalized_input.get("payload") or {})
    bridge_decision = _clean_text(payload.get("decision"), default="BLOCK").upper()
    packet_type = _normalize_name(governance_packet.get("packet_type"))
    runtime_context = _normalize_runtime_context(
        payload.get("runtime_context") or governance_packet.get("runtime_context")
    )
    execution_intent = _normalize_name(
        governance_packet.get("execution_intent") or input_payload.get("execution_intent"),
        default="respond",
    )
    normalized_requested_provider = _derive_requested_provider(input_payload, requested_provider)
    normalized_requested_provider_mode = _derive_requested_provider_mode(
        input_payload,
        requested_provider_mode,
    )

    phase_gate = _phase_gate_status(runtime_context)
    module_governance_gate = _module_governance_status(module_governance_controller)
    verification_gate = _build_verification_gate(
        bridge_decision=bridge_decision,
        packet_type=packet_type,
        execution_intent=execution_intent,
    )

    if phase_gate["decision"] == "BLOCK":
        return _blocked_envelope(
            bridge_result=payload,
            runtime_context=runtime_context,
            bridge_decision=bridge_decision,
            packet_type=packet_type,
            requested_provider=normalized_requested_provider,
            requested_provider_mode=normalized_requested_provider_mode,
            reason="phase_gate_blocked",
            notes=["governed_llm_not_admitted_in_runtime_context"],
            phase_gate=phase_gate,
            module_governance_gate=module_governance_gate,
            verification_gate=verification_gate,
        )

    if module_governance_gate["decision"] == "BLOCK":
        return _blocked_envelope(
            bridge_result=payload,
            runtime_context=runtime_context,
            bridge_decision=bridge_decision,
            packet_type=packet_type,
            requested_provider=normalized_requested_provider,
            requested_provider_mode=normalized_requested_provider_mode,
            reason="module_governance_blocked",
            notes=["governed_llm_module_is_not_admitted"],
            phase_gate=phase_gate,
            module_governance_gate=module_governance_gate,
            verification_gate=verification_gate,
        )

    if verification_gate["decision"] == "BLOCK":
        return _blocked_envelope(
            bridge_result=payload,
            runtime_context=runtime_context,
            bridge_decision=bridge_decision,
            packet_type=packet_type,
            requested_provider=normalized_requested_provider,
            requested_provider_mode=normalized_requested_provider_mode,
            reason="verification_gate_blocked",
            notes=["governed_llm_boundary_rules_failed"],
            phase_gate=phase_gate,
            module_governance_gate=module_governance_gate,
            verification_gate=verification_gate,
        )

    wonder_verdict = payload.get("wonder_verdict")
    if wonder_verdict is None and packet_type in {
        "generation_request",
        "deliberation_request",
        "reasoning_packet_ingress",
    }:
        try:
            from src.otem_capability import get_otem_capability_level
            from src.wonder.validation import evaluate_bridge_ingress_wonder

            wonder_verdict = evaluate_bridge_ingress_wonder(
                normalized_input,
                governance_packet,
                otem_level=get_otem_capability_level(),
            )
        except Exception:
            wonder_verdict = {"verdict": "forbid", "violations": [{"code": "wonder_evaluator_fault"}]}

    try:
        from src.otem_capability import get_otem_capability_level
        from src.wonder.gate import wonder_allows_escalation

        if wonder_verdict and not wonder_allows_escalation(
            wonder_verdict,
            otem_level=get_otem_capability_level(),
        ):
            return _blocked_envelope(
                bridge_result=payload,
                runtime_context=runtime_context,
                bridge_decision=bridge_decision,
                packet_type=packet_type,
                requested_provider=normalized_requested_provider,
                requested_provider_mode=normalized_requested_provider_mode,
                reason="wonder_gate_blocked",
                notes=["wonder_gate_blocked_downstream"],
                phase_gate=phase_gate,
                module_governance_gate=module_governance_gate,
                verification_gate=verification_gate,
            )
    except Exception:
        return _blocked_envelope(
            bridge_result=payload,
            runtime_context=runtime_context,
            bridge_decision=bridge_decision,
            packet_type=packet_type,
            requested_provider=normalized_requested_provider,
            requested_provider_mode=normalized_requested_provider_mode,
            reason="wonder_gate_blocked",
            notes=["wonder_gate_evaluator_fault"],
            phase_gate=phase_gate,
            module_governance_gate=module_governance_gate,
            verification_gate=verification_gate,
        )

    registry = provider_registry_instance or provider_registry
    preferred_provider = normalized_requested_provider or _provider_from_mode(normalized_requested_provider_mode)
    route = resolve_model_route(
        response_mode=_default_response_mode(packet_type, input_payload),
        tool_type=_clean_text(input_payload.get("tool_type")) or None,
        preferred_provider=preferred_provider,
        provider_available=registry.can_invoke,
    )
    provider_request = {
        "route_id": route["id"],
        "response_mode": route["response_mode"],
        "provider": route["provider"],
        "provider_label": route["provider_label"],
        "provider_kind": route["provider_kind"],
        "provider_model": route.get("provider_model"),
        "execution_backend": route["execution_backend"],
        "instruction": route["instruction"],
        "generation_overrides": dict(route.get("generation_overrides") or {}),
        "surface_identity": route.get("surface_identity"),
        "authority_lane": route.get("authority_lane"),
        "execution_intent": execution_intent,
    }
    provider_resolution = {
        "requested_provider": preferred_provider,
        "requested_provider_mode": normalized_requested_provider_mode,
        "resolved_provider": route["provider"],
        "provider_reason": route["provider_reason"],
        "provider_label": route["provider_label"],
        "provider_kind": route["provider_kind"],
        "provider_model": route.get("provider_model"),
        "execution_backend": route["execution_backend"],
        "available": bool(registry.get_config(route["provider"])),
    }
    notes: list[str] = []
    if bridge_decision == "DEGRADE":
        notes.append("bridge_entered_degraded_posture")
    if preferred_provider and route["provider"] != preferred_provider:
        notes.append("preferred_provider_was_not_available_and_route_fell_back")

    trace = [
        {"stage": "bridge_received", "value": bridge_decision},
        {"stage": "phase_gate", "value": dict(phase_gate)},
        {"stage": "module_governance", "value": dict(module_governance_gate)},
        {"stage": "provider_route", "value": dict(provider_resolution)},
        {"stage": "verification_gate", "value": dict(verification_gate)},
        {"stage": "proposal_commit", "value": "PROPOSED"},
    ]
    from src.aais_ul.runtime import wrap_runtime_snapshot

    return wrap_runtime_snapshot(
        {
            "module_id": GOVERNED_LLM_MODULE_ID,
            "version": GOVERNED_LLM_MODULE_VERSION,
            "status": "PROPOSED",
            "reason": "bounded_provider_proposal_ready",
            "proposal_only": True,
            "execution_authority": "none",
            "mutation_authority": "none",
            "bounded_envelope": True,
            "runtime_context": runtime_context,
            "bridge_decision": bridge_decision,
            "packet_type": packet_type,
            "requested_provider": preferred_provider,
            "requested_provider_mode": normalized_requested_provider_mode,
            "provider_resolution": provider_resolution,
            "provider_request": provider_request,
            "phase_gate": phase_gate,
            "module_governance": module_governance_gate,
            "verification_gate": verification_gate,
            "allowed_output_shape": list(GOVERNED_LLM_ALLOWED_OUTPUT_SHAPE),
            "declared_transitions": list(GOVERNED_LLM_DECLARED_TRANSITIONS),
            "notes": notes,
            "trace": trace,
            "bridge_result_fingerprint": _fingerprint(payload),
        }
    )


def validate_governed_llm_envelope(payload: dict[str, Any] | None) -> bool:
    """Return whether the output still honors the bounded governed seam contract."""
    if not isinstance(payload, dict):
        return False
    if payload.get("module_id") != GOVERNED_LLM_MODULE_ID:
        return False
    if payload.get("version") != GOVERNED_LLM_MODULE_VERSION:
        return False
    if payload.get("status") not in {"PROPOSED", "BLOCKED"}:
        return False
    if payload.get("proposal_only") is not True:
        return False
    if payload.get("execution_authority") != "none":
        return False
    if payload.get("mutation_authority") != "none":
        return False
    if payload.get("bounded_envelope") is not True:
        return False
    if not isinstance(payload.get("trace"), list):
        return False
    if not isinstance(payload.get("allowed_output_shape"), list):
        return False
    return True
