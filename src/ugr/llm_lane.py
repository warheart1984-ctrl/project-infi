"""UGR governed LLM lane v1 — proposal-only, temperature 0, invariant gated."""

# Mythic: Llm Lane
# Engineering: LlmLane
from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from hashlib import sha256
import json
import os
import time
from pathlib import Path
from typing import Any

from src.aais_governed_llm_module import (
    GOVERNED_LLM_MODULE_ID,
    propose_governed_llm_envelope,
    validate_governed_llm_envelope,
)
from src.invariant_engine import InvariantEngine
from src.jarvis_detachment_guard import build_bridge_attestation
from src.ugr.lane_manager import LaneResult, LaneSpec
from src.ugr.governed_llm_executor import execute_governed_llm_proposal, llm_execution_enabled
from src.decode_governance_executor import execute_with_decode_governance


UGR_LLM_LANE_VERSION = "1.0"
UGR_LLM_TEMPERATURE = 0.0
UGR_LLM_GENERATION_OVERRIDES = {
    "temperature": UGR_LLM_TEMPERATURE,
    "temperature_max": UGR_LLM_TEMPERATURE,
}


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _normalize_question(question: str) -> str:
    return " ".join(str(question or "").split()).strip().lower()


def _runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


def build_bridge_result_for_llm_lane(shared_context: dict[str, Any]) -> dict[str, Any]:
    """Reuse UGR bridge clearance when present; otherwise synthesize deliberation clearance."""
    existing = shared_context.get("bridge_result")
    if isinstance(existing, dict) and existing:
        return dict(existing)

    question = str(shared_context.get("question") or "").strip()
    intent = str(shared_context.get("intent") or "general_qa").strip().lower()
    trace_id = str(shared_context.get("trace_id") or "ugr-llm-lane")
    context = dict(shared_context.get("context") or {})
    payload = {
        "question": question[:500],
        "intent": intent,
        "execution_intent": "observe",
        "trace_id": trace_id,
        "response_mode": "think",
        "provider_mode": str(context.get("provider_mode") or "local_first"),
        "generation_overrides": dict(UGR_LLM_GENERATION_OVERRIDES),
        "bridge_attestation": build_bridge_attestation(
            ingress="ugr_runtime",
            surface="ugr_llm_lane",
            source_id=trace_id,
            route="ugr.llm_lane",
            intent="observe",
            runtime_context="live_runtime",
            packet_type="deliberation_request",
            runtime_dir=_runtime_dir(),
        ),
    }
    normalized_input = {
        "source": "ugr_runtime",
        "type": "deliberation_request",
        "payload": payload,
    }
    governance_packet = {
        "source": "ugr_runtime",
        "packet_type": "deliberation_request",
        "execution_intent": "observe",
        "runtime_context": "live_runtime",
        "effectful": False,
        "risk": str(context.get("risk") or "low"),
    }
    return _wrap_ul_payload({
        "decision": "ALLOW",
        "runtime_context": "live_runtime",
        "execution_allowed": True,
        "normalized_input": normalized_input,
        "governance_packet": governance_packet,
    })


def apply_ugr_temperature_cap(provider_request: dict[str, Any] | None) -> dict[str, Any]:
    capped = dict(provider_request or {})
    overrides = dict(capped.get("generation_overrides") or {})
    overrides.update(UGR_LLM_GENERATION_OVERRIDES)
    capped["generation_overrides"] = overrides
    return capped


def _temperature_invariant(provider_request: dict[str, Any] | None) -> dict[str, Any]:
    overrides = dict((provider_request or {}).get("generation_overrides") or {})
    temperature = float(overrides.get("temperature", overrides.get("temperature_max", 1.0)))
    temperature_max = float(overrides.get("temperature_max", temperature))
    if temperature <= UGR_LLM_TEMPERATURE and temperature_max <= UGR_LLM_TEMPERATURE:
        return _wrap_ul_payload({
            "name": "temperature_zero",
            "status": "pass",
            "details": f"temperature={temperature}, temperature_max={temperature_max}",
        })
    return _wrap_ul_payload({
        "name": "temperature_zero",
        "status": "hard_fail",
        "details": f"UGR LLM lane requires temperature 0; got temperature={temperature}, temperature_max={temperature_max}",
    })


def validate_llm_lane_invariants(
    envelope: dict[str, Any],
    *,
    bridge_result: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    normalized = dict(bridge_result.get("normalized_input") or {})
    governance = dict(bridge_result.get("governance_packet") or {})
    existing_invariant = bridge_result.get("bridge_invariant")
    if isinstance(existing_invariant, dict) and existing_invariant.get("status") == "pass":
        bridge_status = "pass"
    else:
        bridge_invariant = InvariantEngine.validate_bridge_packet(normalized, governance)
        bridge_status = str(bridge_invariant.get("status") or "fail")
    results.append(
        {
            "name": "bridge_invariant",
            "status": "pass" if bridge_status == "pass" else "hard_fail",
            "details": bridge_status,
        }
    )

    if validate_governed_llm_envelope(envelope):
        results.append({"name": "governed_llm_envelope", "status": "pass", "details": envelope.get("status")})
    else:
        results.append(
            {
                "name": "governed_llm_envelope",
                "status": "hard_fail",
                "details": "envelope shape invalid",
            }
        )

    if envelope.get("proposal_only") is True:
        results.append({"name": "proposal_only", "status": "pass", "details": "ok"})
    else:
        results.append({"name": "proposal_only", "status": "hard_fail", "details": "lane must remain proposal-only"})

    capped_request = apply_ugr_temperature_cap(dict(envelope.get("provider_request") or {}))
    results.append(_temperature_invariant(capped_request))
    return results


def _deterministic_hypothesis(question: str, intent: str, envelope: dict[str, Any]) -> str:
    route = dict(envelope.get("provider_request") or {})
    seed = _stable_json(
        {
            "question": _normalize_question(question),
            "intent": intent,
            "route_id": route.get("route_id"),
            "provider": route.get("provider"),
            "response_mode": route.get("response_mode"),
            "module_id": envelope.get("module_id"),
        }
    )
    digest = sha256(seed.encode("utf-8")).hexdigest()[:8]
    instruction = str(route.get("instruction") or "Inspect governed trace and pattern ledger before action.")
    return f"Governed proposal ({digest}): {instruction[:160]}"


def _claim(
    *,
    claim_id: str,
    subject: str,
    predicate: str,
    object_value: str,
    confidence: float,
    source_lane: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return _wrap_ul_payload({
        "id": claim_id,
        "subject": subject,
        "predicate": predicate,
        "object": object_value,
        "confidence": round(max(0.0, min(1.0, float(confidence))), 3),
        "source_type": source_lane,
        "evidence_refs": list(evidence_refs or []),
    })


def build_llm_lane_claims(
    spec: LaneSpec,
    shared_context: dict[str, Any],
    envelope: dict[str, Any],
    *,
    confidence_scale: float = 1.0,
    execution: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    question = str(shared_context.get("question") or "").strip()
    intent = str(shared_context.get("intent") or "general_qa").strip().lower()
    if not question:
        return []

    fingerprint = str(envelope.get("bridge_result_fingerprint") or "unknown")
    route = dict(envelope.get("provider_request") or {})
    hypothesis = _deterministic_hypothesis(question, intent, envelope)
    evidence_refs = [f"governed_llm:{fingerprint}", f"route:{route.get('route_id') or 'unknown'}"]
    if execution and execution.get("status") == "EXECUTED":
        hypothesis = str(execution.get("content") or hypothesis)[:800]
        evidence_refs.append(f"execution:{execution.get('executor_version') or '1.0'}")
        evidence_refs.append(f"provider:{execution.get('provider') or 'unknown'}")
    claims = [
        _claim(
            claim_id=f"{spec.lane_id}-llm-primary",
            subject=question[:80],
            predicate="suggested_next_step",
            object_value=hypothesis,
            confidence=0.72 * confidence_scale,
            source_lane="llm",
            evidence_refs=evidence_refs,
        ),
        _claim(
            claim_id=f"{spec.lane_id}-llm-status",
            subject=question[:80],
            predicate="governed_llm_status",
            object_value=str(envelope.get("status") or "UNKNOWN"),
            confidence=0.9 * confidence_scale,
            source_lane="llm",
            evidence_refs=[GOVERNED_LLM_MODULE_ID, str(envelope.get("reason") or "")],
        ),
    ]
    return claims


def _immune_flags(shared_context: dict[str, Any], envelope: dict[str, Any]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    context = dict(shared_context.get("context") or {})
    if bool(shared_context.get("immune_elevated") or context.get("immune_elevated")):
        flags.append(
            {
                "type": "immune_elevated",
                "severity": "medium",
                "details": "UGR LLM lane running under elevated immune posture",
            }
        )
    if envelope.get("status") == "BLOCKED":
        flags.append(
            {
                "type": "governed_llm_blocked",
                "severity": "high",
                "details": str(envelope.get("reason") or "governed_llm_blocked"),
            }
        )
    return flags


def run_governed_llm_lane(
    spec: LaneSpec,
    shared_context: dict[str, Any],
    *,
    module_governance_controller: Any | None = None,
    provider_registry_instance: Any | None = None,
    force_execute: bool = False,
) -> LaneResult:
    """Run governed LLM lane — proposal envelope with optional governed execution."""
    started = time.perf_counter()
    bridge_result = build_bridge_result_for_llm_lane(shared_context)
    envelope = propose_governed_llm_envelope(
        bridge_result,
        module_governance_controller=module_governance_controller,
    )
    invariant_results = validate_llm_lane_invariants(envelope, bridge_result=bridge_result)
    immune_flags = _immune_flags(shared_context, envelope)

    capped_request = apply_ugr_temperature_cap(dict(envelope.get("provider_request") or {}))
    envelope = dict(envelope)
    envelope["provider_request"] = capped_request

    hard_fail = any(item.get("status") == "hard_fail" for item in invariant_results)
    blocked = envelope.get("status") == "BLOCKED" or hard_fail
    confidence_scale = 0.75 if immune_flags else 1.0

    execution: dict[str, Any] | None = None
    tokens_used = 0
    claims: list[dict[str, Any]] = []
    if not blocked:
        ir = bridge_result.get("governance_ir")
        bundle = bridge_result.get("decode_governance_bundle")
        if not ir or not bundle:
            try:
                from src.governance_ir import build_governance_ir
                from src.invariant_compiler import compile_from_ir

                ir = build_governance_ir(bridge_result=bridge_result)
                bundle = compile_from_ir(ir)
            except Exception:
                ir = None
                bundle = None
        session_id = str(
            shared_context.get("session_id")
            or (shared_context.get("context") or {}).get("session_id")
            or ""
        )
        if ir and bundle:
            execution = execute_with_decode_governance(
                envelope,
                bridge_result=bridge_result,
                question=str(shared_context.get("question") or ""),
                provider_registry_instance=provider_registry_instance,
                force_execute=force_execute,
                governance_ir=ir,
                decode_bundle=bundle,
                session_id=session_id or None,
            )
        else:
            execution = execute_governed_llm_proposal(
                envelope,
                bridge_result=bridge_result,
                question=str(shared_context.get("question") or ""),
                provider_registry_instance=provider_registry_instance,
                force_execute=force_execute,
            )
        if execution.get("status") == "EXECUTED":
            tokens_used = int(execution.get("tokens_used") or 0)
        claims = build_llm_lane_claims(
            spec,
            shared_context,
            envelope,
            confidence_scale=confidence_scale,
            execution=execution,
        )

    duration_ms = int((time.perf_counter() - started) * 1000)
    status = "blocked" if blocked else "success"
    payload: dict[str, Any] = {
        "claims": claims,
        "governed_llm": envelope,
    }
    if execution is not None:
        payload["governed_llm_execution"] = execution
    payload["llm_execution_enabled"] = llm_execution_enabled() or force_execute
    return LaneResult(
        lane_id=spec.lane_id,
        lane_type=spec.lane_type,
        status=status,
        metrics={
            "duration_ms": duration_ms,
            "tokens_used": tokens_used,
            "llm_lane_version": UGR_LLM_LANE_VERSION,
            "governed_llm_status": envelope.get("status"),
            "execution_status": (execution or {}).get("status"),
        },
        invariant_results=invariant_results,
        immune_flags=immune_flags,
        payload=payload,
    )
