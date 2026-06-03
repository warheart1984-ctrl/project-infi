"""Rail selection and cognition plan construction."""

# Mythic: Rails
# Engineering: RailsEngine
from __future__ import annotations

from typing import Any

from src.cloud_forge.failsafe import failsafe_force_safe
from src.cloud_forge.risk import estimate_novelty, estimate_risk
from src.cloud_forge.types import (
    CACHE_MODES,
    RAIL_STEP_CHAINS,
    CLAIM_ASSERTED,
    ClusterState,
    CognitionPlan,
    GovernanceWeight,
    LawEnvelope,
    PerformanceProfile,
    Rail,
    RailDecision,
    RiskLevel,
    TaskSignature,
    cap_cache_mode,
    cap_rail_at_ceiling,
)


def _law_ceiling_for(risk: RiskLevel, law: LawEnvelope) -> Rail:
    if risk == RiskLevel.HIGH or law.required_proof:
        return Rail.SAFE
    if risk == RiskLevel.MEDIUM or law.forbid_express:
        return Rail.NORMAL
    return Rail.EXPRESS


def choose_rail(
    task: TaskSignature,
    actor: GovernanceWeight,
    tenant: PerformanceProfile,
    cluster: ClusterState | None = None,
    law_envelope: LawEnvelope | None = None,
    *,
    immune_elevated: bool = False,
    force_safe: bool | None = None,
    pattern_records: list[dict] | None = None,
) -> RailDecision:
    """Select SAFE / NORMAL / EXPRESS per contract selection algorithm."""
    _ = cluster
    law = law_envelope or LawEnvelope(law_id="unknown", law_version="unknown")
    risk = estimate_risk(task, law)
    novelty = estimate_novelty(task, pattern_records)
    codes: list[str] = []

    if risk == RiskLevel.HIGH:
        codes.append("risk.high")
    elif risk == RiskLevel.MEDIUM:
        codes.append("risk.medium")
    else:
        codes.append("risk.low")

    active_force_safe = failsafe_force_safe() if force_safe is None else force_safe
    if active_force_safe:
        codes.append("failsafe.force_safe")

    if immune_elevated:
        codes.append("immune.elevated")

    if law.required_proof:
        codes.append("law.required_proof")

    if law.forbid_express:
        codes.append("law.forbid_express")

    law_ceiling = _law_ceiling_for(risk, law)

    if (
        risk == RiskLevel.HIGH
        or law.required_proof
        or active_force_safe
        or immune_elevated
    ):
        return RailDecision(
            task_id=task.task_id,
            rail=Rail.SAFE,
            risk=risk,
            novelty=novelty,
            rationale_codes=codes,
            law_ceiling=law_ceiling,
        )

    rail = Rail.NORMAL if risk == RiskLevel.MEDIUM else Rail.EXPRESS
    rail = cap_rail_at_ceiling(rail, law_ceiling)

    if actor.wL < tenant.wL_express_floor:
        if rail == Rail.EXPRESS:
            rail = Rail.NORMAL
        codes.append("weight.express_denied")

    if (
        actor.wL >= tenant.wL_express_threshold
        and tenant.latency_bias >= 0.35
        and law_ceiling == Rail.EXPRESS
        and rail == Rail.NORMAL
    ):
        rail = Rail.EXPRESS
        codes.append("weight.express_granted")

    return RailDecision(
        task_id=task.task_id,
        rail=rail,
        risk=risk,
        novelty=novelty,
        rationale_codes=codes,
        law_ceiling=law_ceiling,
    )


def _select_model_tier(
    rail: Rail,
    actor: GovernanceWeight,
    tenant: PerformanceProfile,
    cluster: ClusterState | None,
) -> str:
    availability = (cluster or ClusterState()).model_availability
    if rail == Rail.EXPRESS and actor.effective_wI < tenant.wL_express_threshold:
        return "tiny" if availability.get("tiny", True) else "mid"
    if tenant.intelligence_bias >= 0.4 and availability.get("big", True):
        return "big"
    return "mid" if availability.get("mid", True) else "tiny"


def _select_parallelism(rail: Rail, actor: GovernanceWeight) -> int:
    if rail == Rail.SAFE:
        return 1
    if rail == Rail.NORMAL:
        return 2
    return min(16, max(2, 2 + int(actor.effective_wT // 50)))


def _select_cache_mode(rail: Rail, law: LawEnvelope) -> str:
    if rail == Rail.SAFE:
        base = "off"
    elif rail == Rail.NORMAL:
        base = "L0"
    else:
        base = "L1"
    return cap_cache_mode(base, law.forbid_cache_above)


def _select_speculation(rail: Rail, actor: GovernanceWeight, law: LawEnvelope) -> str:
    if law.forbid_speculation or rail == Rail.SAFE:
        return "off"
    if rail == Rail.EXPRESS and actor.wL >= 100:
        return "aggressive"
    return "light"


def build_plan(
    task: TaskSignature,
    decision: RailDecision,
    actor: GovernanceWeight,
    tenant: PerformanceProfile,
    cluster: ClusterState | None = None,
    law_envelope: LawEnvelope | None = None,
) -> CognitionPlan:
    """Build CognitionPlan for a chosen rail."""
    law = law_envelope or LawEnvelope(law_id="unknown", law_version="unknown")
    rail = decision.rail
    domain_template = task.domain if rail == Rail.EXPRESS else None

    return CognitionPlan(
        task_id=task.task_id,
        rail=rail,
        steps=list(RAIL_STEP_CHAINS[rail]),
        model_tier=_select_model_tier(rail, actor, tenant, cluster),
        parallelism=_select_parallelism(rail, actor),
        cache_mode=_select_cache_mode(rail, law),
        speculation=_select_speculation(rail, actor, law),
        domain_template=domain_template,
        claim_status=CLAIM_ASSERTED,
    )


def schedule_request(
    task: TaskSignature | dict[str, Any],
    actor: GovernanceWeight | dict[str, Any],
    tenant: PerformanceProfile | dict[str, Any],
    cluster: ClusterState | dict[str, Any] | None = None,
    law_envelope: LawEnvelope | dict[str, Any] | None = None,
    *,
    immune_elevated: bool = False,
    force_safe: bool | None = None,
    pattern_records: list[dict] | None = None,
) -> dict[str, Any]:
    """Choose rail, build plan, return cloud_forge bundle for pipeline attachment."""
    task_obj = task if isinstance(task, TaskSignature) else TaskSignature.from_dict(task)
    actor_obj = actor if isinstance(actor, GovernanceWeight) else GovernanceWeight.from_dict(actor)
    tenant_obj = tenant if isinstance(tenant, PerformanceProfile) else PerformanceProfile.from_dict(tenant)
    cluster_obj = (
        None
        if cluster is None
        else cluster
        if isinstance(cluster, ClusterState)
        else ClusterState.from_dict(cluster)
    )
    law_obj = (
        None
        if law_envelope is None
        else law_envelope
        if isinstance(law_envelope, LawEnvelope)
        else LawEnvelope.from_dict(law_envelope)
    )

    decision = choose_rail(
        task_obj,
        actor_obj,
        tenant_obj,
        cluster_obj,
        law_obj,
        immune_elevated=immune_elevated,
        force_safe=force_safe,
        pattern_records=pattern_records,
    )
    plan = build_plan(task_obj, decision, actor_obj, tenant_obj, cluster_obj, law_obj)
    return {
        "contract_version": decision.contract_version,
        "rail_decision": decision.to_dict(),
        "cognition_plan": plan.to_dict(),
    }


def attach_cloud_forge_to_pipeline(
    pipeline: dict[str, Any],
    cloud_forge_context: dict[str, Any],
) -> dict[str, Any]:
    """Attach rail_decision + cognition_plan (+ optional ledger) to pipeline dict."""
    from src.cloud_forge.integration import schedule_request_observed

    use_observed = bool(
        cloud_forge_context.get("log_ledger", True)
        or cloud_forge_context.get("apply_domain_template", True)
        or cloud_forge_context.get("domain")
        or (cloud_forge_context.get("task") or {}).get("domain")
    )
    if use_observed:
        bundle = schedule_request_observed(
            task=cloud_forge_context.get("task") or {},
            actor=cloud_forge_context.get("actor") or {},
            tenant=cloud_forge_context.get("tenant") or {},
            cluster=cloud_forge_context.get("cluster"),
            law_envelope=cloud_forge_context.get("law_envelope"),
            immune_elevated=bool(cloud_forge_context.get("immune_elevated")),
            force_safe=cloud_forge_context.get("force_safe"),
            log_ledger=bool(cloud_forge_context.get("log_ledger", True)),
            submit_promotion=bool(cloud_forge_context.get("submit_promotion", True)),
            outcome_summary=cloud_forge_context.get("outcome_summary"),
            tenant_id=str(cloud_forge_context.get("tenant_id") or "default"),
            apply_domain_template=bool(cloud_forge_context.get("apply_domain_template", True)),
        )
    else:
        bundle = schedule_request(
            task=cloud_forge_context.get("task") or {},
            actor=cloud_forge_context.get("actor") or {},
            tenant=cloud_forge_context.get("tenant") or {},
            cluster=cloud_forge_context.get("cluster"),
            law_envelope=cloud_forge_context.get("law_envelope"),
            immune_elevated=bool(cloud_forge_context.get("immune_elevated")),
            force_safe=cloud_forge_context.get("force_safe"),
        )
    updated = dict(pipeline)
    updated["cloud_forge"] = bundle
    if bundle.get("cloud_forge_readout"):
        updated["cloud_forge_readout"] = bundle["cloud_forge_readout"]
    return updated


def validate_cache_mode(mode: str) -> bool:
    return mode in CACHE_MODES
