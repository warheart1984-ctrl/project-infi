"""Cloud Forge rail scheduling for UGR deliberation traces."""

from __future__ import annotations

from hashlib import sha256
import os
from typing import Any

from src.cloud_forge.rails import schedule_request
from src.cloud_forge.types import CONTRACT_VERSION, PerformanceProfile
from src.ugr.platform.tenant_registry import normalize_tenant_id


UGR_CLOUD_FORGE_ENABLED_ENV = "UGR_CLOUD_FORGE_ENABLED"
UGR_CLOUD_FORGE_OBSERVED_ENV = "UGR_CLOUD_FORGE_OBSERVED"
UGR_LAW_ID = "AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW"
UGR_DOMAIN_PREFIX = "ugr"


def cloud_forge_enabled() -> bool:
    raw = os.getenv(UGR_CLOUD_FORGE_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def cloud_forge_observed() -> bool:
    raw = os.getenv(UGR_CLOUD_FORGE_OBSERVED_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _normalize_question(question: str) -> str:
    return " ".join(str(question or "").split()).strip().lower()


def _prompt_hash(question: str) -> str:
    normalized = _normalize_question(question)
    if not normalized:
        return ""
    return sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _mutation_scope(intent: str, context: dict[str, Any]) -> str:
    scope = str(context.get("mutation_scope") or "").strip().lower()
    if scope in {"none", "read", "write", "constitutional"}:
        return scope
    intent_key = str(intent or "").strip().lower()
    if intent_key in {"deploy", "apply_patch", "mutate", "write"}:
        return "write"
    if context.get("violates_policy") or context.get("constitutional"):
        return "constitutional"
    return "read"


def _law_signals(intent: str, context: dict[str, Any]) -> list[str]:
    signals = ["read_only", "ugr_deliberate"]
    intent_key = str(intent or "").strip().lower()
    if intent_key.startswith("docs") or intent_key in {"general_qa", "explain"}:
        signals.append("docs")
    if context.get("required_proof"):
        signals.append("constitutional")
    return signals


def build_ugr_task_signature(
    request: dict[str, Any],
    *,
    trace_id: str,
) -> dict[str, Any]:
    intent = str(request.get("intent") or "general_qa").strip().lower()
    question = str(request.get("question") or "").strip()
    context = dict(request.get("context") or {})
    return {
        "task_id": trace_id,
        "pattern_class": intent,
        "mutation_scope": _mutation_scope(intent, context),
        "domain": f"{UGR_DOMAIN_PREFIX}/{intent}",
        "normalized_prompt_hash": _prompt_hash(question),
        "tool_intents": [str(item) for item in (context.get("tool_intents") or []) if str(item).strip()],
        "context_text": question[:500],
    }


def build_ugr_law_envelope(request: dict[str, Any]) -> dict[str, Any]:
    intent = str(request.get("intent") or "general_qa").strip().lower()
    context = dict(request.get("context") or {})
    required_proof = bool(context.get("required_proof") or context.get("constitutional"))
    forbid_express = bool(context.get("forbid_express") or required_proof)
    return {
        "law_id": UGR_LAW_ID,
        "law_version": "1",
        "forbid_express": forbid_express,
        "forbid_cache_above": context.get("forbid_cache_above"),
        "forbid_speculation": bool(context.get("forbid_speculation") or required_proof),
        "required_proof": required_proof,
        "signals": _law_signals(intent, context),
    }


def _immune_elevated(request: dict[str, Any], bridge_result: dict[str, Any] | None) -> bool:
    if bool(request.get("immune_elevated")):
        return True
    context = dict(request.get("context") or {})
    if bool(context.get("immune_elevated")):
        return True
    if not bridge_result:
        return False
    governance = dict(bridge_result.get("governance") or {})
    if str(governance.get("risk") or "low").strip().lower() not in {"low", ""}:
        return True
    if str(bridge_result.get("immune_response") or "ALLOW").strip().upper() != "ALLOW":
        return True
    return False


def build_ugr_actor(request: dict[str, Any]) -> dict[str, Any]:
    actor = dict(request.get("cloud_forge_actor") or {})
    return {
        "wL": float(actor.get("wL", 100)),
        "wT": actor.get("wT"),
        "wI": actor.get("wI"),
        "tier": str(actor.get("tier") or "ugr"),
    }


def build_ugr_tenant_profile(request: dict[str, Any]) -> dict[str, Any]:
    profile = dict(request.get("cloud_forge_tenant") or {})
    if profile:
        return profile
    default = PerformanceProfile()
    return {
        "latency_bias": default.latency_bias,
        "throughput_bias": default.throughput_bias,
        "intelligence_bias": default.intelligence_bias,
        "wL_express_threshold": default.wL_express_threshold,
        "wL_express_floor": default.wL_express_floor,
    }


def rail_trace_summary(bundle: dict[str, Any] | None) -> dict[str, Any]:
    if not bundle:
        return {}
    decision = dict(bundle.get("rail_decision") or {})
    plan = dict(bundle.get("cognition_plan") or {})
    return {
        "contract_version": bundle.get("contract_version") or decision.get("contract_version") or CONTRACT_VERSION,
        "rail": decision.get("rail"),
        "risk": decision.get("risk"),
        "novelty": decision.get("novelty"),
        "law_ceiling": decision.get("law_ceiling"),
        "rationale_codes": list(decision.get("rationale_codes") or []),
        "cache_mode": plan.get("cache_mode"),
        "model_tier": plan.get("model_tier"),
        "parallelism": plan.get("parallelism"),
    }


def schedule_rail_for_ugr(
    request: dict[str, Any],
    *,
    trace_id: str,
    bridge_result: dict[str, Any] | None = None,
    pattern_records: list[dict] | None = None,
) -> dict[str, Any] | None:
    """Schedule Cloud Forge rail for one UGR deliberation request."""
    if not cloud_forge_enabled():
        return None

    task = build_ugr_task_signature(request, trace_id=trace_id)
    law_envelope = build_ugr_law_envelope(request)
    immune_elevated = _immune_elevated(request, bridge_result)

    if cloud_forge_observed():
        from src.cloud_forge.integration import schedule_request_observed

        tenant_id = normalize_tenant_id(request.get("tenant_id"))
        return schedule_request_observed(
            task=task,
            actor=build_ugr_actor(request),
            tenant=build_ugr_tenant_profile(request),
            cluster=dict(request.get("cloud_forge_cluster") or {}),
            law_envelope=law_envelope,
            immune_elevated=immune_elevated,
            force_safe=request.get("cloud_forge_force_safe"),
            log_ledger=bool(request.get("cloud_forge_log_ledger", True)),
            submit_promotion=bool(request.get("cloud_forge_submit_promotion", False)),
            tenant_id=tenant_id,
            apply_domain_template=bool(request.get("cloud_forge_apply_template", False)),
        )

    return schedule_request(
        task=task,
        actor=build_ugr_actor(request),
        tenant=build_ugr_tenant_profile(request),
        cluster=dict(request.get("cloud_forge_cluster") or {}),
        law_envelope=law_envelope,
        immune_elevated=immune_elevated,
        force_safe=request.get("cloud_forge_force_safe"),
        pattern_records=pattern_records,
    )


def attach_cloud_forge_metadata(response: dict[str, Any], bundle: dict[str, Any] | None) -> dict[str, Any]:
    """Attach Cloud Forge bundle and slim rail_decision alias to a UGR response."""
    if not bundle:
        return response
    from src.aais_ul_substrate import attach_ul_substrate, wrap_cloud_forge_bundle

    updated = dict(response)
    wrapped_bundle = wrap_cloud_forge_bundle(dict(bundle))
    updated["cloud_forge"] = wrapped_bundle
    updated["rail_decision"] = dict(bundle.get("rail_decision") or {})
    if wrapped_bundle.get("ul_substrate"):
        updated["ul_substrate"] = wrapped_bundle["ul_substrate"]
        updated["ul_trace"] = wrapped_bundle["ul_trace"]
    return attach_ul_substrate(updated)
