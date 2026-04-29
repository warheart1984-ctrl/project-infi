"""Shared cognitive ingress bridge for governed AAIS runtime decisions.

The bridge normalizes inbound runtime intent into one packet shape, derives a
deterministic governance packet, and runs a bounded law/invariant pass before
live execution continues.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any

from src.aris_integration import build_aris_enforcement
from src.governed_event_chain import governed_event
from src.immune_system import ImmuneSystemController, immune_system


BRIDGE_ID = "aais.cognitive_bridge"
BRIDGE_VERSION = "0.1"
APPROVAL_REQUIRED_PACKET_TYPES = {
    "runtime_action_execute",
    "repo_change_execute",
    "tool_execution",
    "capability_execution",
}
EFFECTFUL_PACKET_TYPES = {
    "runtime_action_execute",
    "repo_change_execute",
    "tool_execution",
    "capability_execution",
}
MODEL_ONLY_SOURCES = {"llm", "predictor", "swarm"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
DECISION_ALLOW = "ALLOW"
DECISION_DEGRADE = "DEGRADE"
DECISION_BLOCK = "BLOCK"


class CognitiveBridgeValidationError(ValueError):
    """Raised when a packet is missing bridge-required structure."""


@dataclass(frozen=True)
class GovernancePacket:
    """Deterministic governance view of one routed input."""

    bridge_id: str
    bridge_version: str
    packet_fingerprint: str
    source: str
    packet_type: str
    intent: str
    execution_intent: str
    runtime_context: str
    lane: str
    risk: str
    requires_approval: bool
    approval_granted: bool
    effectful: bool
    payload_fingerprint: str
    doctrine_path: tuple[str, ...]
    invariants: tuple[str, ...]
    bounded: bool = True


def _clean_text(value: Any, default: str = "") -> str:
    return " ".join(str(value or "").replace("-", "_").split()).strip().lower() or default


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _fingerprint(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()[:16]


def _normalize_runtime_context(value: Any) -> str:
    normalized = _clean_text(value, "live_runtime")
    return normalized or "live_runtime"


def _normalize_risk(value: Any) -> str:
    normalized = _clean_text(value, "low")
    aliases = {
        "minimal": "low",
        "safe": "low",
        "normal": "low",
        "moderate": "medium",
        "elevated": "high",
        "severe": "critical",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in RISK_LEVELS else "low"


def _normalize_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _clean_text(value)
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _normalize_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CognitiveBridgeValidationError("payload must be a JSON object")
    return dict(payload)


def _is_effectful(packet_type: str, payload: dict[str, Any]) -> bool:
    if packet_type in EFFECTFUL_PACKET_TYPES:
        return True
    if _normalize_bool(payload.get("repo_change")):
        return True
    return _clean_text(payload.get("execution_intent")) == "execute"


def _default_requires_approval(packet_type: str, payload: dict[str, Any]) -> bool:
    if packet_type in APPROVAL_REQUIRED_PACKET_TYPES:
        return True
    return _normalize_bool(payload.get("repo_change"))


def _derive_execution_intent(packet_type: str, payload: dict[str, Any]) -> str:
    explicit = _clean_text(payload.get("execution_intent"))
    if explicit:
        return explicit
    if packet_type in EFFECTFUL_PACKET_TYPES:
        return "execute"
    if packet_type in {"signal_evaluation", "reasoning_packet_ingress"}:
        return "observe"
    if packet_type in {"generation_request", "deliberation_request"}:
        return "respond"
    return "route"


def _derive_intent(packet_type: str, payload: dict[str, Any], execution_intent: str) -> str:
    explicit = _clean_text(payload.get("intent"))
    if explicit:
        return explicit
    if packet_type == "reasoning_packet_ingress":
        return "evaluate"
    if execution_intent == "execute":
        return "execute"
    if packet_type in {"generation_request", "operator_turn"}:
        return "respond"
    if packet_type == "signal_evaluation":
        return "observe"
    return "route"


def _derive_lane(effectful: bool, requires_approval: bool) -> str:
    if effectful or requires_approval:
        return "service_tools"
    return "direct_cognitive"


def _derive_doctrine_path(
    packet_type: str,
    payload: dict[str, Any],
    effectful: bool,
    requires_approval: bool,
) -> tuple[str, ...]:
    path = [
        "meaning_before_execution",
        "defined_law_before_mutation",
        "bounded_behavior_before_flow",
        "aris_embedded_runtime_boundary",
    ]
    if effectful:
        path.append("verification_before_finalize")
    if requires_approval:
        path.append("approval_before_effectful_execution")
    if packet_type == "reasoning_packet_ingress":
        path.append("ingress_validation_before_admission")
    if packet_type in {"generation_request", "deliberation_request"}:
        path.append("governed_llm_after_bridge")
    if payload.get("external_suggestion") or payload.get("external_suggestion_present"):
        path.append("non_copy_clause_before_admission")
    return tuple(path)


def _derive_invariants(
    *,
    source: str,
    packet_type: str,
    payload: dict[str, Any],
    effectful: bool,
    requires_approval: bool,
) -> tuple[str, ...]:
    invariants = [
        "packet_shape_complete",
        "payload_present",
        "runtime_context_explicit",
        "governance_packet_emitted",
        "structured_trace_emitted",
        "aris_runtime_boundary_enforced",
        "aris_does_not_self_apply",
    ]
    if effectful:
        invariants.extend(
            [
                "effectful_execution_is_governed",
                "verification_alignment_required",
            ]
        )
    if requires_approval:
        invariants.append("approval_state_declared")
    if source in MODEL_ONLY_SOURCES:
        invariants.append("model_only_sources_cannot_self_execute")
    if packet_type == "reasoning_packet_ingress":
        invariants.append("ingress_protocol_checked")
    if packet_type in {"generation_request", "deliberation_request"}:
        invariants.append("governed_llm_proposal_required")
    if payload.get("external_suggestion") or payload.get("external_suggestion_present"):
        invariants.append("non_copy_clause_enforced")
    if any(
        key in payload
        for key in (
            "pattern_share_mode",
            "collective_share_mode",
            "export_mode",
            "share_mode",
            "content_transfer_mode",
        )
    ):
        invariants.append("shared_patterns_are_signature_only")
    return tuple(invariants)


def _normalize_input_packet(
    raw: dict[str, Any] | None,
    *,
    runtime_context: str,
) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise CognitiveBridgeValidationError("input packet must be a JSON object")
    source = _clean_text(raw.get("source"))
    packet_type = _clean_text(raw.get("type"))
    if not source:
        raise CognitiveBridgeValidationError("input packet source is required")
    if not packet_type:
        raise CognitiveBridgeValidationError("input packet type is required")
    payload = _normalize_payload(raw.get("payload"))
    requires_approval = _normalize_bool(
        raw.get("requires_approval"),
        default=_default_requires_approval(packet_type, payload),
    )
    approval_granted = _normalize_bool(payload.get("approval_granted"))
    risk = _normalize_risk(raw.get("risk"))
    normalized_context = _normalize_runtime_context(raw.get("runtime_context") or runtime_context)
    execution_intent = _derive_execution_intent(packet_type, payload)
    effectful = _is_effectful(packet_type, payload)
    if effectful and "verification_required" not in payload:
        payload["verification_required"] = True
    payload.setdefault("execution_intent", execution_intent)
    payload.setdefault("runtime_context", normalized_context)
    return {
        "source": source,
        "type": packet_type,
        "payload": payload,
        "requires_approval": requires_approval,
        "approval_granted": approval_granted,
        "risk": risk,
        "runtime_context": normalized_context,
        "execution_intent": execution_intent,
        "effectful": effectful,
    }


def _system_state_for_risk(risk: str) -> dict[str, str]:
    if risk == "critical":
        return {"system_mode": "degraded", "risk_level": "high"}
    if risk == "high":
        return {"system_mode": "caution", "risk_level": "high"}
    if risk == "medium":
        return {"system_mode": "caution", "risk_level": "medium"}
    return {"system_mode": "stable", "risk_level": "low"}


def _posture_signal_for_risk(risk: str) -> str:
    if risk == "low":
        return "stable_posture"
    if risk == "medium":
        return "caution_posture"
    return "elevated_posture"


def _build_governed_event_feed(packet: dict[str, Any], governance: GovernancePacket) -> dict[str, Any]:
    runtime_context = governance.runtime_context
    active_lane = "service_tools" if governance.lane == "service_tools" else "direct_cognitive"
    traffic_class = "service" if active_lane == "service_tools" else "core_cognition"
    runtime_signal_class = (
        "operator_runtime_active" if runtime_context == "operator_runtime" else "live_runtime_active"
    )
    service_packet_count = 1 if active_lane == "service_tools" else 0
    forward_packet_count = 0 if active_lane == "service_tools" else 1
    return_packet_count = 1
    total_packet_count = service_packet_count + forward_packet_count + return_packet_count
    signals = [
        {
            "signal_type": "runtime_boundary",
            "signal_class": runtime_signal_class,
            "stable_key": f"runtime_boundary:{runtime_context}",
            "severity": "low",
            "status": "observed",
            "data_sufficiency": "sufficient",
            "attributes": {"runtime_context": runtime_context},
        },
        {
            "signal_type": "lane_activity",
            "signal_class": "service_lane_active" if active_lane == "service_tools" else "direct_lane_active",
            "stable_key": f"lane_activity:{active_lane}",
            "severity": "low",
            "status": "observed",
            "data_sufficiency": "sufficient",
            "attributes": {"active_lane": active_lane},
        },
        {
            "signal_type": "system_posture",
            "signal_class": _posture_signal_for_risk(governance.risk),
            "stable_key": f"system_posture:{governance.risk}",
            "severity": governance.risk,
            "status": "observed",
            "data_sufficiency": "sufficient",
            "attributes": _system_state_for_risk(governance.risk),
        },
        {
            "signal_type": "packet_activity",
            "signal_class": "packet_flow_observed",
            "stable_key": f"packet_activity:{governance.packet_type}:{total_packet_count}",
            "severity": "low",
            "status": "observed",
            "data_sufficiency": "sufficient",
            "attributes": {
                "forward_packet_count": forward_packet_count,
                "service_packet_count": service_packet_count,
                "return_packet_count": return_packet_count,
                "total_packet_count": total_packet_count,
                "forward_intents": [governance.intent] if forward_packet_count else [],
                "service_intents": [governance.packet_type] if service_packet_count else [],
                "return_intents": ["ack"],
            },
        },
    ]
    if governance.effectful or governance.requires_approval:
        signals.append(
            {
                "signal_type": "tool_activity",
                "signal_class": "service_tool_completed",
                "stable_key": f"tool_activity:{governance.packet_type}",
                "severity": governance.risk,
                "status": "observed",
                "data_sufficiency": "sufficient",
                "attributes": {
                    "tool_type": governance.packet_type,
                    "requires_approval": governance.requires_approval,
                    "approval_granted": governance.approval_granted,
                },
            }
        )
    signals.append(
        {
            "signal_type": "turn_delta",
            "signal_class": "baseline_only",
            "stable_key": "turn_delta:baseline",
            "severity": "low",
            "status": "delta",
            "data_sufficiency": "sufficient",
            "attributes": {
                "has_previous_turn": False,
                "runtime_context_changed": False,
                "lane_changed": False,
                "traffic_class_changed": False,
                "response_mode_changed": False,
                "contract_changed": False,
                "tool_changed": governance.effectful or governance.requires_approval,
                "immune_response_changed": False,
                "system_mode_changed": governance.risk != "low",
                "risk_level_changed": governance.risk != "low",
                "surface_node_changed": False,
                "change_count": 1 if governance.effectful or governance.risk != "low" else 0,
                "stable_repeat": False,
            },
        }
    )
    return {
        "source_pipeline_id": f"{BRIDGE_ID}:{governance.packet_fingerprint}",
        "runtime_context": runtime_context,
        "active_lane": active_lane,
        "traffic_class": traffic_class,
        "surface_node": "jar",
        "immune_response": "ALLOW",
        "tool_type": governance.packet_type if governance.effectful else None,
        "signal_count": len(signals),
        "signals": signals,
        "packet_metrics": {
            "forward_packet_count": forward_packet_count,
            "service_packet_count": service_packet_count,
            "return_packet_count": return_packet_count,
            "total_packet_count": total_packet_count,
            "forward_intents": [governance.intent] if forward_packet_count else [],
            "service_intents": [governance.packet_type] if service_packet_count else [],
            "return_intents": ["ack"],
        },
        "delta": dict(signals[-1]["attributes"]),
        "validation": {
            "runtime_context_explicit": True,
            "signal_shape_uniform": True,
            "signal_count_bounded": True,
            "signal_count_matches": True,
            "stable_keys_unique": True,
            "turn_delta_present": True,
            "delta_shape_complete": True,
            "packet_metrics_complete": True,
        },
        "system_state": _system_state_for_risk(governance.risk),
    }


def _build_governance_packet(packet: dict[str, Any]) -> GovernancePacket:
    doctrine_path = _derive_doctrine_path(
        packet["type"],
        packet["payload"],
        packet["effectful"],
        packet["requires_approval"],
    )
    invariants = _derive_invariants(
        source=packet["source"],
        packet_type=packet["type"],
        payload=packet["payload"],
        effectful=packet["effectful"],
        requires_approval=packet["requires_approval"],
    )
    intent = _derive_intent(packet["type"], packet["payload"], packet["execution_intent"])
    payload_fingerprint = _fingerprint(packet["payload"])
    packet_fingerprint = _fingerprint(
        {
            "source": packet["source"],
            "type": packet["type"],
            "payload": packet["payload"],
            "requires_approval": packet["requires_approval"],
            "approval_granted": packet["approval_granted"],
            "risk": packet["risk"],
            "runtime_context": packet["runtime_context"],
        }
    )
    return GovernancePacket(
        bridge_id=BRIDGE_ID,
        bridge_version=BRIDGE_VERSION,
        packet_fingerprint=packet_fingerprint,
        source=packet["source"],
        packet_type=packet["type"],
        intent=intent,
        execution_intent=packet["execution_intent"],
        runtime_context=packet["runtime_context"],
        lane=_derive_lane(packet["effectful"], packet["requires_approval"]),
        risk=packet["risk"],
        requires_approval=packet["requires_approval"],
        approval_granted=packet["approval_granted"],
        effectful=packet["effectful"],
        payload_fingerprint=payload_fingerprint,
        doctrine_path=doctrine_path,
        invariants=invariants,
    )


def summarize_bridge_result(result: dict[str, Any] | None) -> str:
    """Return a compact one-line summary for logs and UI traces."""
    payload = dict(result or {})
    governance = dict(payload.get("governance_packet") or {})
    summary = payload.get("summary")
    if summary:
        return str(summary)
    packet_type = governance.get("packet_type", "packet")
    source = governance.get("source", "unknown_source")
    decision = payload.get("decision", DECISION_BLOCK)
    return f"Cognitive Bridge routed {packet_type} from {source} with decision {decision}."


class CognitiveBridgeService:
    """Normalize ingress, derive doctrine/invariants, and fail closed when needed."""

    def __init__(self, *, immune_controller: ImmuneSystemController | None = None):
        self.immune_controller = immune_controller or immune_system

    def route_to_bridge(
        self,
        input_packet: dict[str, Any] | None,
        *,
        runtime_context: str = "live_runtime",
    ) -> dict[str, Any]:
        normalized = _normalize_input_packet(input_packet, runtime_context=runtime_context)
        governance = _build_governance_packet(normalized)
        aris_enforcement = build_aris_enforcement(
            details=normalized["payload"],
            runtime_context=governance.runtime_context,
            effectful=governance.effectful,
            source=governance.source,
            packet_type=governance.packet_type,
        )
        event_feed = _build_governed_event_feed(normalized, governance)
        governed = governed_event(
            event_feed,
            runtime_context=governance.runtime_context,
            immune_controller=self.immune_controller,
        )

        reasons: list[str] = []
        notes: list[str] = []
        decision = DECISION_ALLOW
        execution_allowed = True

        if governed.get("decision") == DECISION_BLOCK:
            decision = DECISION_BLOCK
            execution_allowed = False
            reasons.append("governed_event_blocked")

        if governance.effectful and governance.source in MODEL_ONLY_SOURCES:
            decision = DECISION_BLOCK
            execution_allowed = False
            reasons.append("model_only_source_cannot_execute")

        if governance.effectful and governance.requires_approval and not governance.approval_granted:
            decision = DECISION_BLOCK
            execution_allowed = False
            reasons.append("approval_missing_for_effectful_execution")

        if decision != DECISION_BLOCK and governance.effectful and governance.risk in {"high", "critical"}:
            decision = DECISION_DEGRADE
            notes.append("high_risk_effectful_execution")

        if decision != DECISION_BLOCK and not governance.effectful and governance.risk == "critical":
            decision = DECISION_DEGRADE
            notes.append("critical_risk_non_effectful_input")

        if aris_enforcement["status"] == "blocked":
            decision = DECISION_BLOCK
            execution_allowed = False
            reasons.append("aris_non_copy_clause")

        status = {
            DECISION_ALLOW: "ready",
            DECISION_DEGRADE: "degraded_ready",
            DECISION_BLOCK: "blocked",
        }[decision]

        if decision == DECISION_BLOCK:
            if "aris_non_copy_clause" in reasons:
                summary = (
                    "Cognitive Bridge blocked execution because the ARIS non-copy clause "
                    "detected raw or private material that cannot move into governed flow."
                )
            else:
                summary = (
                    "Cognitive Bridge blocked execution because law context was missing, "
                    "incomplete, or not allowed to execute."
                )
        elif decision == DECISION_DEGRADE:
            summary = (
                "Cognitive Bridge allowed the packet under elevated scrutiny and reduced trust."
            )
        else:
            summary = "Cognitive Bridge normalized the packet and cleared it for governed flow."

        result = {
            "bridge_id": BRIDGE_ID,
            "version": BRIDGE_VERSION,
            "decision": decision,
            "status": status,
            "summary": summary,
            "execution_allowed": execution_allowed,
            "runtime_context": governance.runtime_context,
            "requires_approval": governance.requires_approval,
            "approval_granted": governance.approval_granted,
            "risk": governance.risk,
            "normalized_input": normalized,
            "governance_packet": asdict(governance),
            "doctrine_path": list(governance.doctrine_path),
            "invariants": list(governance.invariants),
            "aris_enforcement": aris_enforcement,
            "event_feed": event_feed,
            "governed_event": governed,
            "reason_codes": reasons,
            "notes": notes,
            "trace": [
                {"stage": "intent", "value": governance.intent},
                {"stage": "doctrine", "value": list(governance.doctrine_path)},
                {"stage": "invariants", "value": list(governance.invariants)},
                {"stage": "aris", "value": aris_enforcement},
                {"stage": "governance_packet", "value": asdict(governance)},
                {"stage": "decision", "value": decision},
            ],
        }
        if governance.packet_type in {"generation_request", "deliberation_request"}:
            from src.aais_governed_llm_module import propose_governed_llm_envelope

            governed_llm = propose_governed_llm_envelope(result)
            result["governed_llm"] = governed_llm
            result["trace"].append(
                {
                    "stage": "governed_llm",
                    "value": {
                        "status": governed_llm.get("status"),
                        "reason": governed_llm.get("reason"),
                        "provider": ((governed_llm.get("provider_request") or {}).get("provider")),
                    },
                }
            )
            if governed_llm.get("status") == "BLOCKED":
                result["decision"] = DECISION_BLOCK
                result["status"] = "blocked"
                result["summary"] = (
                    "Cognitive Bridge blocked execution because the governed LLM seam "
                    "did not clear the packet."
                )
                result["execution_allowed"] = False
                result["reason_codes"] = [*result["reason_codes"], "governed_llm_blocked"]
            else:
                result["notes"] = [*result["notes"], "governed_llm_proposal_ready"]
            result["trace"].append({"stage": "final_decision", "value": result["decision"]})
        return result


def route_to_bridge(
    input_packet: dict[str, Any] | None,
    *,
    runtime_context: str = "live_runtime",
    immune_controller: ImmuneSystemController | None = None,
) -> dict[str, Any]:
    """Route one packet through the shared cognitive bridge."""
    service = CognitiveBridgeService(immune_controller=immune_controller)
    return service.route_to_bridge(input_packet, runtime_context=runtime_context)
