"""Admission policy evaluation."""

from __future__ import annotations

from typing import Any

from platform.mesh.policy import evaluate_mesh_policy
from platform.policy.compile import build_admission_context, compile_rules, evaluate_compiled_rules
from platform.policy.plans import PLAN_TEMPLATES
from platform.store import PlatformStore


def load_org_policy(org: dict[str, Any] | None) -> dict[str, Any]:
    if not org:
        return dict(PLAN_TEMPLATES["free"])
    plan_id = str(org.get("plan_id") or "free")
    base = dict(PLAN_TEMPLATES.get(plan_id, PLAN_TEMPLATES["free"]))
    overrides = dict(org.get("policy") or {})
    base.update(overrides)
    base["policy_version"] = "platform.org_policy.v1"
    base["org_id"] = str(org.get("org_id") or "")
    base["plan_id"] = plan_id
    base.setdefault("region", org.get("region") or "us")
    base.setdefault("data_residency", org.get("data_residency") or base["region"])
    return base


def evaluate_admission(
    *,
    org: dict[str, Any] | None,
    job_request: dict[str, Any],
    running_jobs: int = 0,
    jobs_today: int = 0,
) -> tuple[bool, str]:
    policy = load_org_policy(org)
    subsystem = str(job_request.get("subsystem") or "")
    job_type = str(job_request.get("job_type") or job_request.get("kind", "").split(".")[-1])

    if subsystem == "slingshot" and not policy.get("slingshot_enabled"):
        return False, "slingshot disabled for plan"
    allowed_sub = policy.get("allowed_subsystems") or []
    if allowed_sub and subsystem not in allowed_sub:
        return False, f"subsystem {subsystem} not allowed"
    allowed_types = policy.get("allowed_job_types") or []
    if allowed_types and job_type not in allowed_types:
        return False, f"job_type {job_type} not allowed"
    if running_jobs >= int(policy.get("max_concurrent_jobs") or 1):
        return False, "max concurrent jobs exceeded"
    if jobs_today >= int(policy.get("jobs_per_day") or 1000):
        return False, "daily job quota exceeded"
    from platform.sovereign.profile import get_sovereign_profile

    profile = get_sovereign_profile(org)
    residency = str(profile.get("data_residency") or policy.get("data_residency") or "us")
    region = str(job_request.get("region") or (org.get("region") if org else "us"))
    if residency and region and residency != region:
        return False, f"data residency mismatch: requires {residency}"
    return True, "ok"


def evaluate_dsl_admission(
    *,
    store: PlatformStore | None,
    org: dict[str, Any] | None,
    job_request: dict[str, Any],
    principal_role: str = "operator",
) -> tuple[bool, str]:
    if not store or not org:
        return True, "ok"
    rules = store.list_policy_rules(org_id=str(org.get("org_id") or ""))
    if not rules:
        dsl_source = str((org.get("policy_dsl") or {}).get("rules_source") or "")
        if not dsl_source:
            return True, "ok"
        predicates, _, _ = compile_rules(org_id=str(org["org_id"]), source=dsl_source)
    else:
        source = "\n".join(str(r.get("source") or "") for r in rules)
        predicates, _, _ = compile_rules(org_id=str(org["org_id"]), source=source)
    ctx = build_admission_context(org=org, job_request=job_request, principal_role=principal_role)
    return evaluate_compiled_rules(predicates, ctx=ctx)


def mesh_blocks_slingshot(*, store: PlatformStore, org_id: str, job_request: dict[str, Any]) -> tuple[bool, str]:
    if str(job_request.get("kind") or "") != "slingshot.launch":
        return True, "ok"
    mok, mreason = evaluate_mesh_policy(
        store=store,
        org_id=org_id,
        job_kind="slingshot.launch",
    )
    if not mok:
        return False, mreason
    for job in store.list_jobs(org_id=org_id):
        if job.get("proof_required") and job.get("proof_status") != "proven":
            if job.get("status") in {"complete", "cancelled"}:
                continue
            if not job.get("assignee_principal_id"):
                on_call = store.get_on_call(org_id)
                if on_call and (on_call.get("principal_ids") or []):
                    return True, "ok"
                return False, "proof-required job needs assignee or on-call before slingshot.launch"
    return True, "ok"


def drift_blocks_slingshot(*, store: PlatformStore, org_id: str) -> tuple[bool, str]:
    for job in store.list_jobs(org_id=org_id, subsystem="drift_detector"):
        if job.get("kind") == "drift_investigation" and job.get("status") not in {"complete", "cancelled"}:
            return False, "open drift_investigation blocks slingshot.launch"
        meta = job.get("metadata") or {}
        for f in meta.get("findings") or []:
            if int(f.get("severity", 0)) >= 3 and job.get("status") not in {"complete"}:
                return False, "high-severity drift blocks slingshot until resolved"
    return True, "ok"
