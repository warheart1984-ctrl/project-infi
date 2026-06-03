"""Cloud Forge rail scheduling for UGR deliberation traces."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from typing import Any

from src.cloud_forge.rails import schedule_request
from src.cloud_forge.types import CONTRACT_VERSION, PerformanceProfile
from src.ugr.platform.tenant_registry import TenantRegistry, TenantSpec, normalize_tenant_id

CLOUD_FORGE_BINDING_VERSION = "3.0"


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


def _derive_express_thresholds_from_cost_ceiling(cost_ceiling: dict[str, Any]) -> tuple[float, float]:
    """Lower URG cost ceiling → stricter Cloud Forge EXPRESS eligibility."""
    hard = float((cost_ceiling or {}).get("hard_ceil") or 100)
    baseline = 100.0
    delta = max(0.0, baseline - hard)
    threshold = 100.0 + delta * 0.5
    floor = 50.0 + delta * 0.25
    return threshold, floor


def build_forge_profile_from_tenant(
    tenant_spec: TenantSpec | str,
    *,
    registry: TenantRegistry | None = None,
) -> dict[str, Any]:
    """Map URG TenantSpec to Cloud Forge PerformanceProfile dict."""
    if isinstance(tenant_spec, str):
        reg = registry or TenantRegistry()
        resolved = reg.get(tenant_spec)
        if resolved is None:
            default = PerformanceProfile()
            return {
                "latency_bias": default.latency_bias,
                "throughput_bias": default.throughput_bias,
                "intelligence_bias": default.intelligence_bias,
                "wL_express_threshold": default.wL_express_threshold,
                "wL_express_floor": default.wL_express_floor,
            }
        tenant_spec = resolved

    explicit = dict(tenant_spec.cloud_forge or {})
    default = PerformanceProfile()
    threshold, floor = _derive_express_thresholds_from_cost_ceiling(
        dict(tenant_spec.cost_ceiling or {})
    )
    return {
        "latency_bias": float(explicit.get("latency_bias", default.latency_bias)),
        "throughput_bias": float(explicit.get("throughput_bias", default.throughput_bias)),
        "intelligence_bias": float(explicit.get("intelligence_bias", default.intelligence_bias)),
        "wL_express_threshold": float(explicit.get("wL_express_threshold", threshold)),
        "wL_express_floor": float(explicit.get("wL_express_floor", floor)),
    }


def build_forge_actor_from_tenant(
    tenant_spec: TenantSpec | str,
    *,
    operator_id: str | None = None,
    registry: TenantRegistry | None = None,
) -> dict[str, Any]:
    """Map URG tenant to Cloud Forge GovernanceWeight dict."""
    if isinstance(tenant_spec, str):
        reg = registry or TenantRegistry()
        resolved = reg.get(tenant_spec)
        if resolved is None:
            return {"wL": 100.0, "wT": None, "wI": None, "tier": "ugr"}
        tenant_spec = resolved

    explicit = dict((tenant_spec.cloud_forge or {}).get("actor") or {})
    if explicit:
        return {
            "wL": float(explicit.get("wL", 100)),
            "wT": explicit.get("wT"),
            "wI": explicit.get("wI"),
            "tier": str(explicit.get("tier") or tenant_spec.tenant_id),
        }
    hard = float((tenant_spec.cost_ceiling or {}).get("hard_ceil") or 100)
    wL = min(200.0, max(60.0, hard * 1.2))
    return {
        "wL": wL,
        "wT": wL * 0.7,
        "wI": wL * 1.1,
        "tier": str(operator_id or tenant_spec.tenant_id.replace(":", "-")),
    }


def resolve_tenant_manifold_for_forge(request: dict[str, Any]) -> Any | None:
    """Resolve TenantManifoldState for Cloud Forge scheduling from request tenant_id."""
    tenant_id = normalize_tenant_id(request.get("tenant_id"))
    spec = TenantRegistry().get(tenant_id)
    if spec is None:
        return None
    from src.ugr.mission.tenant_manifold import build_tenant_manifold

    return build_tenant_manifold(spec)


def compute_cloud_forge_tenant_digest(profile: dict[str, Any], actor: dict[str, Any]) -> str:
    payload = {
        "binding_version": CLOUD_FORGE_BINDING_VERSION,
        "profile": profile,
        "actor": actor,
    }
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def build_ugr_law_envelope(
    request: dict[str, Any],
    *,
    tenant_manifold: Any | None = None,
) -> dict[str, Any]:
    intent = str(request.get("intent") or "general_qa").strip().lower()
    context = dict(request.get("context") or {})
    required_proof = bool(context.get("required_proof") or context.get("constitutional"))
    forbid_express = bool(context.get("forbid_express") or required_proof)
    if tenant_manifold is not None:
        profile_name = str(getattr(tenant_manifold, "invariant_profile", "") or "").strip()
        if profile_name and profile_name != "default":
            required_proof = True
            forbid_express = True
    constraints = dict(request.get("constraints") or {})
    if str(constraints.get("risk_ceiling") or "").lower() in {"low", "medium"}:
        forbid_express = True
    regions = list(getattr(tenant_manifold, "allowed_regions", None) or ())
    if regions:
        context = dict(context)
        context.setdefault("allowed_regions", list(regions))
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


def _resolve_tenant_spec_for_request(
    request: dict[str, Any],
    *,
    tenant_manifold: Any | None = None,
) -> TenantSpec | None:
    if tenant_manifold is not None:
        return TenantRegistry().get(getattr(tenant_manifold, "tenant_id", "global"))
    tenant_id = str(request.get("tenant_id") or "").strip()
    if tenant_id:
        return TenantRegistry().get(tenant_id)
    return None


def build_ugr_actor(
    request: dict[str, Any],
    *,
    tenant_manifold: Any | None = None,
    operator_id: str | None = None,
) -> dict[str, Any]:
    actor = dict(request.get("cloud_forge_actor") or {})
    if actor:
        return {
            "wL": float(actor.get("wL", 100)),
            "wT": actor.get("wT"),
            "wI": actor.get("wI"),
            "tier": str(actor.get("tier") or "ugr"),
        }
    spec = _resolve_tenant_spec_for_request(request, tenant_manifold=tenant_manifold)
    if spec is not None:
        return build_forge_actor_from_tenant(
            spec,
            operator_id=operator_id or str(request.get("operator_id") or ""),
        )
    return {"wL": 100.0, "wT": None, "wI": None, "tier": "ugr"}


def apply_rail_credit_boost_to_forge(
    request: dict[str, Any],
    tenant_profile: dict[str, Any],
    actor: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Apply bounded EXPRESS boost from a validated spend token in request context."""
    meta: dict[str, Any] = {}
    context = dict(request.get("context") or {})
    boost = dict(context.get("rail_credit_boost") or {})
    if not boost:
        return tenant_profile, actor, meta

    from src.ugr.rewards.rail_credit_spend import consume_forge_boost, validate_forge_boost

    ok, reason, token = validate_forge_boost(boost, runtime_dir=runtime_dir)
    if not ok:
        meta["rail_credit_boost"] = {"applied": False, "reason": reason}
        return tenant_profile, actor, meta

    profile = dict(tenant_profile)
    actor_out = dict(actor)
    reduction = float(token.get("threshold_reduction") or 0)
    floor = float(profile.get("wL_express_floor") or 50)
    threshold = float(profile.get("wL_express_threshold") or 100)
    profile["wL_express_threshold"] = max(floor, threshold - reduction)
    wL = float(actor_out.get("wL") or 100)
    actor_out["wL"] = min(200.0, wL + reduction * 0.5)
    consume_forge_boost(boost, runtime_dir=runtime_dir)
    meta["rail_credit_boost"] = {
        "applied": True,
        "spend_id": token.get("spend_id"),
        "threshold_reduction": reduction,
    }
    return profile, actor_out, meta


def build_ugr_tenant_profile(
    request: dict[str, Any],
    *,
    tenant_manifold: Any | None = None,
) -> dict[str, Any]:
    profile = dict(request.get("cloud_forge_tenant") or {})
    if profile:
        return profile
    spec = _resolve_tenant_spec_for_request(request, tenant_manifold=tenant_manifold)
    if spec is not None:
        return build_forge_profile_from_tenant(spec)
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
    tenant_manifold: Any | None = None,
) -> dict[str, Any] | None:
    """Schedule Cloud Forge rail for one UGR deliberation request."""
    if not cloud_forge_enabled():
        return None

    task = build_ugr_task_signature(request, trace_id=trace_id)
    law_envelope = build_ugr_law_envelope(request, tenant_manifold=tenant_manifold)
    immune_elevated = _immune_elevated(request, bridge_result)
    tenant_profile = build_ugr_tenant_profile(request, tenant_manifold=tenant_manifold)
    actor = build_ugr_actor(
        request,
        tenant_manifold=tenant_manifold,
        operator_id=str(request.get("operator_id") or ""),
    )
    runtime_dir = os.getenv("AAIS_RUNTIME_DIR") or None
    tenant_profile, actor, boost_meta = apply_rail_credit_boost_to_forge(
        request,
        tenant_profile,
        actor,
        runtime_dir=runtime_dir,
    )

    if cloud_forge_observed():
        from src.cloud_forge.integration import schedule_request_observed

        from src.ugr.mission.tenant_manifold import tenant_path_slug

        tenant_id = tenant_path_slug(
            normalize_tenant_id(
                getattr(tenant_manifold, "tenant_id", None) or request.get("tenant_id")
            )
        )
        observed_bundle = schedule_request_observed(
            task=task,
            actor=actor,
            tenant=tenant_profile,
            cluster=dict(request.get("cloud_forge_cluster") or {}),
            law_envelope=law_envelope,
            immune_elevated=immune_elevated,
            force_safe=request.get("cloud_forge_force_safe"),
            log_ledger=bool(request.get("cloud_forge_log_ledger", True)),
            submit_promotion=bool(request.get("cloud_forge_submit_promotion", False)),
            tenant_id=tenant_id,
            apply_domain_template=bool(request.get("cloud_forge_apply_template", False)),
        )
        if observed_bundle is not None and boost_meta:
            observed_bundle = dict(observed_bundle)
            observed_bundle["rail_credit_boost"] = dict(
                boost_meta.get("rail_credit_boost") or boost_meta
            )
        return observed_bundle

    bundle = schedule_request(
        task=task,
        actor=actor,
        tenant=tenant_profile,
        cluster=dict(request.get("cloud_forge_cluster") or {}),
        law_envelope=law_envelope,
        immune_elevated=immune_elevated,
        force_safe=request.get("cloud_forge_force_safe"),
        pattern_records=pattern_records,
    )
    if bundle is not None and boost_meta:
        bundle = dict(bundle)
        bundle["rail_credit_boost"] = dict(boost_meta.get("rail_credit_boost") or boost_meta)
    return bundle


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
