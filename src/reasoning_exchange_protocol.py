"""Bounded reasoning exchange protocol for external packet admission.

This module defines a neutral reasoning envelope and a predictable handshake
for submitting structured reasoning into AAIS without weakening local law.
The shared layer only covers packet shape and ingress behavior. Admission,
rejection, and any downstream use remain local decisions.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from datetime import datetime
from src.datetime_compat import UTC
from typing import Any
from uuid import UUID

from src.immune_system import ImmuneSystemController, immune_system
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
from src.verification_gate import VerificationTestResult, evaluate_verification_gate


REASONING_EXCHANGE_PROTOCOL_ID = "aais.reasoning_exchange"
REASONING_EXCHANGE_PROTOCOL_VERSION = "1.0"
REASONING_EXCHANGE_PACKET_TYPE = "reasoning_packet"
REASONING_EXCHANGE_COMPONENT_ID = "aais.reasoning_exchange_protocol"
REASONING_EXCHANGE_ALLOWED_CONTEXTS = [
    "live_runtime",
    "operator_runtime",
    "test_harness",
]

MAX_CLAIM_LENGTH = 480
MAX_REASONING_LENGTH = 2400
MAX_SOURCE_LENGTH = 120
MAX_DOMAIN_LENGTH = 120
MAX_TAG_LENGTH = 48
MAX_TAG_COUNT = 8
MAX_EVIDENCE_COUNT = 8
MAX_EVIDENCE_ITEM_LENGTH = 280
PARTIAL_CONFIDENCE_THRESHOLD = 0.35
ADMIT_CONFIDENCE_THRESHOLD = 0.70

_TOP_LEVEL_KEYS = {"version", "type", "id", "timestamp", "payload", "meta"}
_PAYLOAD_KEYS = {"claim", "reasoning", "evidence", "confidence"}
_META_KEYS = {"source", "domain", "tags"}


class ReasoningExchangeValidationError(ValueError):
    """Raised when a packet fails strict envelope validation."""


def _clean_text(value: Any, *, limit: int) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_runtime_context(value: Any) -> str:
    cleaned = _clean_text(value, limit=80).lower().replace("-", "_").replace(" ", "_")
    return cleaned or "live_runtime"


def _require_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReasoningExchangeValidationError(f"{label} must be a JSON object.")
    return dict(value)


def _ensure_allowed_keys(payload: dict[str, Any], *, allowed: set[str], label: str) -> None:
    extras = sorted(set(payload) - allowed)
    if extras:
        raise ReasoningExchangeValidationError(
            f"{label} contains unsupported fields: {', '.join(extras)}."
        )


def _ensure_required_keys(payload: dict[str, Any], *, required: set[str], label: str) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise ReasoningExchangeValidationError(
            f"{label} is missing required fields: {', '.join(missing)}."
        )


def _normalize_uuid(value: Any) -> str:
    cleaned = _clean_text(value, limit=64)
    if not cleaned:
        raise ReasoningExchangeValidationError("id is required.")
    try:
        return str(UUID(cleaned))
    except ValueError as exc:
        raise ReasoningExchangeValidationError("id must be a valid UUID.") from exc


def _normalize_timestamp(value: Any) -> str:
    cleaned = _clean_text(value, limit=64)
    if not cleaned:
        raise ReasoningExchangeValidationError("timestamp is required.")
    candidate = cleaned[:-1] + "+00:00" if cleaned.endswith("Z") else cleaned
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ReasoningExchangeValidationError("timestamp must be valid ISO8601.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat()


def _normalize_bounded_string(value: Any, *, field_name: str, limit: int) -> str:
    cleaned = " ".join(str(value or "").split()).strip()
    if not cleaned:
        raise ReasoningExchangeValidationError(f"{field_name} is required.")
    if len(cleaned) > limit:
        raise ReasoningExchangeValidationError(f"{field_name} exceeds the {limit}-character limit.")
    return cleaned


def _normalize_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ReasoningExchangeValidationError("payload.confidence must be numeric.") from exc
    if numeric < 0.0 or numeric > 1.0:
        raise ReasoningExchangeValidationError(
            "payload.confidence must stay within the 0.0 to 1.0 range."
        )
    return round(numeric, 2)


def _normalize_evidence(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ReasoningExchangeValidationError("payload.evidence must be a list.")
    if len(value) > MAX_EVIDENCE_COUNT:
        raise ReasoningExchangeValidationError(
            f"payload.evidence may contain at most {MAX_EVIDENCE_COUNT} items."
        )
    evidence: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ReasoningExchangeValidationError("payload.evidence items must be strings.")
        evidence.append(
            _normalize_bounded_string(
                item,
                field_name="payload.evidence item",
                limit=MAX_EVIDENCE_ITEM_LENGTH,
            )
        )
    return evidence


def _normalize_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise ReasoningExchangeValidationError("meta.tags must be a list.")
    if len(value) > MAX_TAG_COUNT:
        raise ReasoningExchangeValidationError(
            f"meta.tags may contain at most {MAX_TAG_COUNT} items."
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ReasoningExchangeValidationError("meta.tags items must be strings.")
        cleaned = _normalize_bounded_string(item, field_name="meta.tags item", limit=MAX_TAG_LENGTH)
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(cleaned)
    return normalized


def normalize_reasoning_exchange_packet(raw: Any) -> dict[str, Any]:
    """Strictly validate and normalize one neutral reasoning packet."""
    packet = _require_mapping(raw, label="Packet")
    _ensure_allowed_keys(packet, allowed=_TOP_LEVEL_KEYS, label="Packet")
    _ensure_required_keys(packet, required=_TOP_LEVEL_KEYS, label="Packet")

    payload = _require_mapping(packet.get("payload"), label="payload")
    _ensure_allowed_keys(payload, allowed=_PAYLOAD_KEYS, label="payload")
    _ensure_required_keys(payload, required=_PAYLOAD_KEYS, label="payload")

    meta = _require_mapping(packet.get("meta"), label="meta")
    _ensure_allowed_keys(meta, allowed=_META_KEYS, label="meta")
    _ensure_required_keys(meta, required={"source", "tags"}, label="meta")

    domain_raw = meta.get("domain")
    domain = None
    if domain_raw not in {None, ""}:
        domain = _normalize_bounded_string(
            domain_raw,
            field_name="meta.domain",
            limit=MAX_DOMAIN_LENGTH,
        )

    return _wrap_ul_payload({
        "version": _normalize_bounded_string(
            packet.get("version"),
            field_name="version",
            limit=16,
        ),
        "type": _normalize_bounded_string(
            packet.get("type"),
            field_name="type",
            limit=48,
        ),
        "id": _normalize_uuid(packet.get("id")),
        "timestamp": _normalize_timestamp(packet.get("timestamp")),
        "payload": {
            "claim": _normalize_bounded_string(
                payload.get("claim"),
                field_name="payload.claim",
                limit=MAX_CLAIM_LENGTH,
            ),
            "reasoning": _normalize_bounded_string(
                payload.get("reasoning"),
                field_name="payload.reasoning",
                limit=MAX_REASONING_LENGTH,
            ),
            "evidence": _normalize_evidence(payload.get("evidence")),
            "confidence": _normalize_confidence(payload.get("confidence")),
        },
        "meta": {
            "source": _normalize_bounded_string(
                meta.get("source"),
                field_name="meta.source",
                limit=MAX_SOURCE_LENGTH,
            ),
            "domain": domain,
            "tags": _normalize_tags(meta.get("tags") or []),
        },
    })


def build_reasoning_exchange_module_spec(
    module_id: str = REASONING_EXCHANGE_COMPONENT_ID,
) -> dict[str, Any]:
    """Return the AAIS module-governance admission spec for the exchange boundary."""
    return _wrap_ul_payload({
        "module_id": module_id,
        "label": "Reasoning Exchange Protocol",
        "lane": "external_reasoning_ingress",
        "declared_scope": [
            "api_reasoning_evaluate",
            "external_reasoning_ingress",
            "verification_gate",
            "module_governance",
            "phase_gate",
        ],
        "declared_surfaces": [
            "live_runtime",
            "operator_runtime",
            "test_harness",
        ],
        "capabilities": [
            "strict_packet_validation",
            "reasoning_packet_normalization",
            "bounded_handshake_response",
            "local_law_admission",
        ],
        "cisiv": {
            "concept": {
                "status": "passed",
                "summary": "Define a neutral envelope for external reasoning admission without introducing shared law.",
            },
            "identity": {
                "status": "passed",
                "summary": "Keep the exchange layer transport-only so truth and validation remain local to AAIS.",
            },
            "structure": {
                "status": "passed",
                "summary": "Validate packets first, then pass normalized packets through verification and governance.",
            },
            "implementation": {
                "status": "implemented",
                "summary": "AAIS exposes a narrow /api/reasoning/evaluate ingress with fail-fast schema checks and bounded outcomes.",
            },
            "verification": {
                "status": "verified",
                "summary": "Coverage proves malformed packets fail fast, unsupported versions reject cleanly, and valid packets stay governed.",
                "evidence": [
                    "pytest tests/test_reasoning_exchange_protocol.py -q",
                    "pytest tests/test_api.py -k reasoning_evaluate -q",
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
    })


def build_reasoning_exchange_reject_response(
    packet: dict[str, Any],
    *,
    reason: str,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    """Return a bounded reject handshake without touching local governance."""
    return _wrap_ul_payload({
        "protocol_id": REASONING_EXCHANGE_PROTOCOL_ID,
        "protocol_version": REASONING_EXCHANGE_PROTOCOL_VERSION,
        "status": "REJECT",
        "reason": reason,
        "confidence_adjustment": 0.0,
        "notes": list(notes or []),
        "packet": packet,
        "verification_gate": None,
        "phase_gate": {
            "decision": "SKIP",
            "component_id": REASONING_EXCHANGE_COMPONENT_ID,
            "runtime_context": None,
            "reason": "Packet was rejected before governed execution.",
        },
        "module_governance": {
            "decision": "SKIP",
            "module_id": REASONING_EXCHANGE_COMPONENT_ID,
            "status": "not_evaluated",
            "reason": "Packet was rejected before governed execution.",
        },
    })


class ReasoningExchangeProtocol:
    """Governed ingress boundary for neutral reasoning packets."""

    def __init__(
        self,
        *,
        component_id: str = REASONING_EXCHANGE_COMPONENT_ID,
        module_governance_controller: ModuleGovernanceController | None = None,
        immune_controller: ImmuneSystemController | None = None,
        actor_id: str = "reasoning_exchange_protocol",
    ):
        self.component_id = _clean_text(component_id, limit=120).lower().replace(" ", "_")
        self.module_governance_controller = module_governance_controller or module_governance
        self.immune_controller = immune_controller or immune_system
        self.actor_id = _clean_text(actor_id, limit=80) or "reasoning_exchange_protocol"

    def evaluate_normalized_packet(
        self,
        packet: dict[str, Any],
        *,
        runtime_context: str | None = None,
    ) -> dict[str, Any]:
        """Evaluate one normalized packet under local AAIS law."""
        context = _normalize_runtime_context(runtime_context)

        phase_gate_payload = self._phase_gate_allow_payload(runtime_context=context)
        if phase_gate_payload["decision"] == "BLOCK":
            return _wrap_ul_payload({
                "protocol_id": REASONING_EXCHANGE_PROTOCOL_ID,
                "protocol_version": REASONING_EXCHANGE_PROTOCOL_VERSION,
                "status": "REJECT",
                "reason": "phase_gate_blocked",
                "confidence_adjustment": 0.0,
                "notes": [phase_gate_payload["reason"]],
                "packet": packet,
                "verification_gate": None,
                "phase_gate": phase_gate_payload,
                "module_governance": {
                    "decision": "SKIP",
                    "module_id": self.component_id,
                    "status": "not_evaluated",
                    "reason": "Phase gate blocked execution before module governance.",
                },
                "immune_update": None,
                "immune_system": self.immune_controller.snapshot(limit_events=6, limit_incidents=3),
            })

        module_payload = self._module_governance_payload()
        if module_payload["decision"] == "BLOCK":
            return _wrap_ul_payload({
                "protocol_id": REASONING_EXCHANGE_PROTOCOL_ID,
                "protocol_version": REASONING_EXCHANGE_PROTOCOL_VERSION,
                "status": "REJECT",
                "reason": "module_governance_blocked",
                "confidence_adjustment": 0.0,
                "notes": [module_payload["reason"]],
                "packet": packet,
                "verification_gate": None,
                "phase_gate": phase_gate_payload,
                "module_governance": module_payload,
                "immune_update": None,
                "immune_system": self.immune_controller.snapshot(limit_events=6, limit_incidents=3),
            })

        verification = self._verification_payload(packet)
        if verification["decision"] == "BLOCK":
            immune_update = self.observe_boundary_signal(
                signal_type="verification_gate_block",
                severity="medium",
                reason="Reasoning packet failed the local verification gate.",
                runtime_context=context,
                packet=packet,
                decision="REJECT",
            )
            return _wrap_ul_payload({
                "protocol_id": REASONING_EXCHANGE_PROTOCOL_ID,
                "protocol_version": REASONING_EXCHANGE_PROTOCOL_VERSION,
                "status": "REJECT",
                "reason": "verification_gate_blocked",
                "confidence_adjustment": 0.0,
                "notes": list(verification["reasons"]),
                "packet": packet,
                "verification_gate": verification,
                "phase_gate": phase_gate_payload,
                "module_governance": module_payload,
                "immune_update": immune_update,
                "immune_system": self.immune_controller.snapshot(limit_events=6, limit_incidents=3),
            })

        handshake = self._admission_handshake(packet)
        immune_update = None
        if handshake["status"] == "PARTIAL":
            immune_update = self.observe_boundary_signal(
                signal_type="packet_requires_review",
                severity="low",
                reason="Reasoning packet requires bounded local review before stronger admission.",
                runtime_context=context,
                packet=packet,
                decision="PARTIAL",
            )
        elif handshake["status"] == "REJECT":
            immune_update = self.observe_boundary_signal(
                signal_type="insufficient_confidence",
                severity="low",
                reason="Reasoning packet stayed below the admission confidence threshold.",
                runtime_context=context,
                packet=packet,
                decision="REJECT",
            )

        return _wrap_ul_payload({
            "protocol_id": REASONING_EXCHANGE_PROTOCOL_ID,
            "protocol_version": REASONING_EXCHANGE_PROTOCOL_VERSION,
            **handshake,
            "packet": packet,
            "verification_gate": verification,
            "phase_gate": phase_gate_payload,
            "module_governance": module_payload,
            "immune_update": immune_update,
            "immune_system": self.immune_controller.snapshot(limit_events=6, limit_incidents=3),
        })

    def _admission_handshake(self, packet: dict[str, Any]) -> dict[str, Any]:
        confidence = float((packet.get("payload") or {}).get("confidence") or 0.0)
        evidence = list((packet.get("payload") or {}).get("evidence") or [])
        domain = ((packet.get("meta") or {}).get("domain") or "").strip()
        tags = list((packet.get("meta") or {}).get("tags") or [])

        adjustment = 0.0
        notes: list[str] = []

        if not evidence:
            adjustment -= 0.15
            notes.append("no_evidence_attached")
        if not domain:
            adjustment -= 0.05
            notes.append("domain_unspecified")
        if not tags:
            notes.append("untagged_packet")

        adjusted_confidence = max(0.0, min(1.0, confidence + adjustment))
        rounded_adjustment = round(adjusted_confidence - confidence, 2)

        if adjusted_confidence >= ADMIT_CONFIDENCE_THRESHOLD:
            status = "ADMIT"
            reason = "packet_meets_ingress_threshold"
        elif adjusted_confidence >= PARTIAL_CONFIDENCE_THRESHOLD:
            status = "PARTIAL"
            reason = "packet_requires_local_review"
        else:
            status = "REJECT"
            reason = "insufficient_confidence_for_admission"
            notes.append("low_confidence")

        return _wrap_ul_payload({
            "status": status,
            "reason": reason,
            "confidence_adjustment": rounded_adjustment,
            "notes": notes,
        })

    def _phase_gate_allow_payload(self, *, runtime_context: str) -> dict[str, Any]:
        try:
            component = get_component(self.component_id)
        except ComponentNotRegisteredError:
            register_component(
                GovernedComponent(
                    component_id=self.component_id,
                    name="Reasoning Exchange Protocol",
                    component_type="reasoning_ingress",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(REASONING_EXCHANGE_ALLOWED_CONTEXTS),
                    notes="Neutral reasoning ingress under local AAIS law.",
                    validation_metadata={"admitted_by": self.actor_id},
                )
            )
            component = get_component(self.component_id)

        try:
            assert_routable(self.component_id, runtime_context)
            assert_executable(self.component_id, runtime_context)
        except PhaseViolationError as exc:
            return _wrap_ul_payload({
                "decision": "BLOCK",
                "component_id": component.component_id,
                "phase": component.phase.value,
                "runtime_context": runtime_context,
                "reason": str(exc),
            })

        return _wrap_ul_payload({
            "decision": "ALLOW",
            "component_id": component.component_id,
            "phase": component.phase.value,
            "runtime_context": runtime_context,
            "allowed_contexts": list(component.allowed_contexts),
            "reason": "Phase gate allows reasoning exchange evaluation.",
        })

    def _module_governance_payload(self) -> dict[str, Any]:
        record = self.module_governance_controller.get_module(self.component_id)
        if record is None:
            admitted = self.module_governance_controller.admit_module(
                build_reasoning_exchange_module_spec(self.component_id),
                actor_id=self.actor_id,
                actor_role="system",
            )
            record = dict(admitted.get("module") or {})
        else:
            record = dict(record)

        status = str(record.get("status") or "").strip().lower() or "unknown"
        allowed = status == "admitted"
        return _wrap_ul_payload({
            "decision": "ALLOW" if allowed else "BLOCK",
            "module_id": self.component_id,
            "status": status,
            "reason": (
                "Module governance allows reasoning exchange evaluation."
                if allowed
                else f"Module governance status '{status}' blocks reasoning exchange evaluation."
            ),
        })

    def _verification_payload(self, packet: dict[str, Any]) -> dict[str, Any]:
        result = VerificationTestResult(
            test_id=f"reasoning_exchange::{packet['id']}",
            law=2,
            intent=2,
            role=2,
            constraint=2,
            drift=2,
            tags=set(),
            is_repeat_test=False,
        )
        evaluation = evaluate_verification_gate([result])
        return _wrap_ul_payload({
            "decision": evaluation.decision.value,
            "reasons": list(evaluation.reasons),
            "failed_tests": list(evaluation.failed_tests),
        })

    def observe_boundary_signal(
        self,
        *,
        signal_type: str,
        severity: str,
        reason: str,
        runtime_context: str | None,
        packet: dict[str, Any] | None = None,
        raw_packet: Any | None = None,
        decision: str | None = None,
    ) -> dict[str, Any]:
        """Emit one immune observation for protocol-boundary anomalies."""
        packet_payload = dict(packet or {}) if isinstance(packet, dict) else {}
        meta = dict(packet_payload.get("meta") or {}) if isinstance(packet_payload.get("meta"), dict) else {}
        payload = dict(packet_payload.get("payload") or {}) if isinstance(packet_payload.get("payload"), dict) else {}
        details = {
            "runtime_context": _normalize_runtime_context(runtime_context),
            "decision": decision,
            "packet_id": packet_payload.get("id"),
            "packet_version": packet_payload.get("version"),
            "packet_type": packet_payload.get("type"),
            "source": meta.get("source"),
            "domain": meta.get("domain"),
            "tag_count": len(list(meta.get("tags") or [])),
            "evidence_count": len(list(payload.get("evidence") or [])),
            "confidence": payload.get("confidence"),
        }
        if raw_packet is not None and packet_payload == {}:
            details["raw_packet_type"] = type(raw_packet).__name__
        return self.immune_controller.observe_protocol_signal(
            component_id=self.component_id,
            signal_type=signal_type,
            severity=severity,
            reason=reason,
            details=details,
        )
