"""Cloud Forge Phase 2 — observe, log, promote, readout."""

from __future__ import annotations

from typing import Any

from src.cloud_forge.cache import (
    CloudForgeCacheStore,
    effective_cache_mode,
    get_default_cache_store,
    persist_cache_outcomes,
    resolve_cache,
)
from src.cloud_forge.ledger import RailDecisionLedger
from src.cloud_forge.promotion import submit_rail_promotion_candidate
from src.cloud_forge.rails import schedule_request
from src.cloud_forge.readout import build_cloud_forge_readout
from src.cloud_forge.templates import apply_task_template_defaults, enrich_plan_with_template
from src.cloud_forge.locality import (
    apply_priority_parallelism_boost,
    build_cloud_placement,
    enrich_cluster_for_domain,
    get_default_prewarm_store,
)
from src.cloud_forge.types import (
    ClusterState,
    GovernanceWeight,
    LawEnvelope,
    PerformanceProfile,
    Rail,
    TaskSignature,
)


def schedule_request_observed(
    task: dict[str, Any] | TaskSignature,
    actor: dict[str, Any],
    tenant: dict[str, Any],
    cluster: dict[str, Any] | None = None,
    law_envelope: dict[str, Any] | None = None,
    *,
    immune_elevated: bool = False,
    force_safe: bool | None = None,
    ledger: RailDecisionLedger | None = None,
    log_ledger: bool = True,
    submit_promotion: bool = True,
    outcome_summary: str | None = None,
    tenant_id: str = "default",
    apply_domain_template: bool = True,
    cache_store: CloudForgeCacheStore | None = None,
    normalized_question: str | None = None,
    store_answer: str | None = None,
    store_plan: bool | None = None,
    use_cache: bool = True,
    session_id: str | None = None,
    apply_cloud_locality: bool = True,
) -> dict[str, Any]:
    """Schedule rails, apply domain template, caches, cloud locality, optionally log."""
    task_obj = task if isinstance(task, TaskSignature) else TaskSignature.from_dict(task)
    if apply_domain_template:
        task_obj = apply_task_template_defaults(task_obj)

    law_obj = (
        LawEnvelope.from_dict(law_envelope)
        if law_envelope
        else LawEnvelope(law_id="unknown", law_version="unknown")
    )
    actor_obj = actor if isinstance(actor, GovernanceWeight) else GovernanceWeight.from_dict(actor)
    tenant_obj = tenant if isinstance(tenant, PerformanceProfile) else PerformanceProfile.from_dict(tenant)

    session_prewarm = None
    if session_id and apply_cloud_locality:
        session_prewarm = get_default_prewarm_store().resolve_or_create(
            tenant_id,
            session_id,
            law_obj,
            tenant_obj,
            actor_obj,
            task_obj.domain,
        )
        bundle_prewarm = {"session_prewarm": session_prewarm}
    else:
        bundle_prewarm = {}

    cluster_state = (
        enrich_cluster_for_domain(task_obj.domain, cluster)
        if apply_cloud_locality
        else (
            cluster
            if isinstance(cluster, ClusterState)
            else ClusterState.from_dict(cluster) if cluster
            else None
        )
    )

    cf_cache = cache_store or get_default_cache_store()
    ledger_store = ledger or RailDecisionLedger()
    pattern_records = ledger_store.read_records(limit=500)

    bundle = schedule_request(
        task_obj,
        actor_obj,
        tenant_obj,
        cluster_state,
        law_envelope,
        immune_elevated=immune_elevated,
        force_safe=force_safe,
        pattern_records=pattern_records,
    )

    decision = bundle.get("rail_decision") or {}
    rail = decision.get("rail")
    plan = dict(bundle.get("cognition_plan") or {})
    plan = enrich_plan_with_template(plan, task_obj.domain, rail or Rail.NORMAL)
    plan["cache_mode"] = effective_cache_mode(str(plan.get("cache_mode") or "off"), law_obj)

    if apply_cloud_locality:
        placement = build_cloud_placement(
            actor=actor_obj,
            tenant=tenant_obj,
            domain=task_obj.domain,
            cluster=cluster_state,
            session_prewarm=session_prewarm,
        )
        plan["parallelism"] = apply_priority_parallelism_boost(
            int(plan.get("parallelism") or 1),
            placement["priority"],
        )
        bundle["cloud_placement"] = placement
        bundle.update(bundle_prewarm)

    bundle["cognition_plan"] = plan

    question = normalized_question or (law_envelope or {}).get("normalized_question")
    if use_cache:
        resolution = resolve_cache(
            tenant_id=tenant_id,
            law=law_obj,
            task=task_obj,
            cache_mode=plan["cache_mode"],
            store=cf_cache,
            normalized_question=question,
        )
        bundle["cache_resolution"] = resolution
        if resolution.get("status") == "hit" and resolution.get("layer") == "L2":
            bundle["cognition_plan"] = dict(resolution.get("cognition_plan") or plan)
        if resolution.get("status") == "hit" and resolution.get("layer") == "L1":
            bundle["cached_answer"] = resolution.get("answer")

    should_store_plan = store_plan if store_plan is not None else plan["cache_mode"] == "L2"
    if store_answer or should_store_plan:
        bundle["cache_persisted"] = persist_cache_outcomes(
            tenant_id=tenant_id,
            law=law_obj,
            task=task_obj,
            cache_mode=plan["cache_mode"],
            cognition_plan=bundle["cognition_plan"],
            store=cf_cache,
            store_answer=store_answer,
            store_plan=should_store_plan,
            normalized_question=question,
        )
    bundle["task_snapshot"] = {
        "task_id": task_obj.task_id,
        "pattern_class": task_obj.pattern_class,
        "domain": task_obj.domain,
        "normalized_prompt_hash": task_obj.normalized_prompt_hash,
        "mutation_scope": task_obj.mutation_scope,
    }

    ledger_record_id = None
    promotion = None
    if log_ledger:
        record = ledger_store.append(
            bundle,
            outcome_summary=outcome_summary,
            tenant_id=tenant_id,
        )
        ledger_record_id = record.get("record_id")
        bundle["ledger_record_id"] = ledger_record_id
        if submit_promotion:
            promotion = submit_rail_promotion_candidate(record)
            bundle["promotion_candidate"] = promotion

    bundle["cloud_forge_readout"] = build_cloud_forge_readout(
        bundle,
        ledger_record_id=ledger_record_id,
        promotion=promotion,
    )
    from src.aais_ul.runtime import wrap_cloud_forge_bundle

    return wrap_cloud_forge_bundle(bundle)


def enrich_preview_with_cloud_forge(
    preview: dict[str, Any],
    cloud_forge_context: dict[str, Any],
) -> dict[str, Any]:
    """Attach Cloud Forge bundle + readout to Jarvis modular preview."""
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
        store_answer=cloud_forge_context.get("store_answer"),
        store_plan=cloud_forge_context.get("store_plan"),
        normalized_question=cloud_forge_context.get("normalized_question"),
        use_cache=bool(cloud_forge_context.get("use_cache", True)),
        session_id=cloud_forge_context.get("session_id"),
        apply_cloud_locality=bool(cloud_forge_context.get("apply_cloud_locality", True)),
    )
    updated = dict(preview)
    updated["cloud_forge"] = bundle
    updated["cloud_forge_readout"] = bundle.get("cloud_forge_readout")
    return updated
