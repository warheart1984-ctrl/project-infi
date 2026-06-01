"""Assistant query — read-only synthesis, no job execution."""

from __future__ import annotations

import os
from typing import Any

from platform.store import PlatformStore


def build_context_bundle(
    *,
    store: PlatformStore,
    org_id: str,
    job_id: str = "",
    max_jobs: int = 10,
    max_artifacts: int = 20,
) -> dict[str, Any]:
    jobs = store.list_jobs(org_id=org_id)
    if job_id:
        j = store.get_job(job_id)
        jobs = [j] if j else []
    else:
        jobs = jobs[:max_jobs]
    artifacts = store.list_artifact_refs(org_id=org_id)[:max_artifacts]
    drift_jobs = [j for j in store.list_jobs(org_id=org_id, subsystem="drift_detector")]
    usage = store.list_usage(org_id=org_id)[:7]
    rules = store.list_policy_rules(org_id=org_id)
    return {
        "org_id": org_id,
        "jobs": jobs,
        "artifacts": artifacts,
        "drift_jobs": drift_jobs[:5],
        "usage": usage,
        "policy_rules_count": len(rules),
    }


def run_assistant_query(
    *,
    store: PlatformStore,
    org_id: str,
    question: str,
    job_id: str = "",
) -> dict[str, Any]:
    ctx = build_context_bundle(store=store, org_id=org_id, job_id=job_id)
    use_llm = os.environ.get("PLATFORM_ASSISTANT_LLM", "0") == "1"
    if use_llm:
        summary = f"LLM slot disabled in CI; question={question[:120]}"
    else:
        n_jobs = len(ctx["jobs"])
        n_art = len(ctx["artifacts"])
        summary = (
            f"Org {org_id}: {n_jobs} job(s) in scope, {n_art} artifact(s), "
            f"{len(ctx['drift_jobs'])} drift job(s). Question: {question[:200]}"
        )
    anomalies = []
    for j in ctx["drift_jobs"]:
        meta = j.get("metadata") or {}
        for f in meta.get("findings") or []:
            anomalies.append(f"{f.get('organ')}: {f.get('message', f.get('code'))}")
    recommendations = []
    if ctx["drift_jobs"]:
        recommendations.append("Review open drift_check / drift_investigation jobs before new slingshot launches.")
    if not ctx["jobs"]:
        recommendations.append("No recent jobs — submit a mechanic.scan to establish baseline.")
    return {
        "summary": summary,
        "recommendations": recommendations,
        "anomalies": anomalies,
        "next_steps": ["Inspect job graph", "Export usage CSV for billing cycle"],
        "claim_label": "asserted",
        "context_job_count": len(ctx["jobs"]),
    }
