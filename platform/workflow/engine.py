"""Workflow run orchestration."""

from __future__ import annotations

from typing import Any, Callable

from platform.jobs.schema import build_job_record
from platform.store import PlatformStore
from platform.workflow.compiler import compile_steps


def start_workflow_run(
    *,
    store: PlatformStore,
    org_id: str,
    workflow: dict[str, Any],
    actor_principal_id: str,
    enqueue: Callable[..., bool],
) -> dict[str, Any]:
    plan = compile_steps(workflow.get("steps") or [])
    parent = build_job_record(
        org_id=org_id,
        subsystem="workflow_engine",
        kind="workflow_run",
        actor_principal_id=actor_principal_id,
        job_type="workflow_run",
        metadata={"workflow_id": workflow["workflow_id"], "plan": plan, "step_index": 0},
    )
    store.upsert_job(parent)
    if plan:
        first = _enqueue_step(
            store=store,
            org_id=org_id,
            parent=parent,
            step=plan[0],
            actor_principal_id=actor_principal_id,
            enqueue=enqueue,
        )
        parent["metadata"]["current_step_job_id"] = first.get("job_id")
        store.upsert_job(parent)
    enqueue(str(parent["job_id"]), region=str(parent.get("region") or "us"))
    return parent


def _enqueue_step(
    *,
    store: PlatformStore,
    org_id: str,
    parent: dict[str, Any],
    step: dict[str, Any],
    actor_principal_id: str,
    enqueue: Callable[..., bool],
) -> dict[str, Any]:
    job = build_job_record(
        org_id=org_id,
        subsystem=step["subsystem"],  # type: ignore[arg-type]
        kind=step["kind"],
        actor_principal_id=actor_principal_id,
        parent_job_id=str(parent["job_id"]),
        correlation_id=str(parent.get("correlation_id") or parent["job_id"]),
        metadata={"params": step.get("params") or {}, "workflow_step": step.get("index")},
    )
    store.upsert_job(job)
    enqueue(str(job["job_id"]), region=str(job.get("region") or "us"))
    return job


def advance_workflow(*, store: PlatformStore, completed_job: dict[str, Any], enqueue: Callable[..., bool]) -> None:
    parent_id = str(completed_job.get("parent_job_id") or "")
    if not parent_id:
        return
    parent = store.get_job(parent_id)
    if not parent or parent.get("kind") != "workflow_run":
        return
    meta = dict(parent.get("metadata") or {})
    plan = meta.get("plan") or []
    idx = int(meta.get("step_index") or 0) + 1
    if idx >= len(plan):
        from platform.jobs.schema import update_job_status

        store.upsert_job(update_job_status(parent, status="complete"))
        return
    next_step = plan[idx]
    from platform.proof.quorum import federation_blocks_workflow_step

    ok, reason = federation_blocks_workflow_step(
        store=store,
        job=parent,
        next_kind=str(next_step.get("kind") or ""),
    )
    if not ok:
        from platform.jobs.schema import update_job_status

        parent = update_job_status(parent, status="blocked_proof", metadata={"block_reason": reason})
        store.upsert_job(parent)
        return
    step_job = _enqueue_step(
        store=store,
        org_id=str(parent["org_id"]),
        parent=parent,
        step=next_step,
        actor_principal_id=str(parent.get("actor_principal_id") or "workflow"),
        enqueue=enqueue,
    )
    meta["step_index"] = idx
    meta["current_step_job_id"] = step_job.get("job_id")
    parent["metadata"] = meta
    store.upsert_job(parent)


def run_workflow(*, store: PlatformStore, job: dict[str, Any]) -> dict[str, Any]:
    from platform.jobs.schema import update_job_status

    meta = job.get("metadata") or {}
    if meta.get("plan"):
        return update_job_status(job, status="running")
    return update_job_status(job, status="complete")
