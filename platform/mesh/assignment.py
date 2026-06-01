"""Job assignment — operational routing only."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.mesh.events import emit_mesh_event
from platform.mesh.policy import evaluate_mesh_policy
from platform.mesh.queue import dequeue_assignee
from platform.store import PlatformStore


def assign_job(
    *,
    store: PlatformStore,
    job_id: str,
    org_id: str,
    assignee_principal_id: str,
    assigned_by: str,
) -> dict[str, Any]:
    if not assignee_principal_id:
        assignee_principal_id = dequeue_assignee(store=store, org_id=org_id)
        if not assignee_principal_id:
            raise PermissionError("assignment queue empty")
    job = store.get_job(job_id)
    if not job or job.get("org_id") != org_id:
        raise PermissionError("job not found")
    ok, reason = evaluate_mesh_policy(
        store=store,
        org_id=org_id,
        assignee_principal_id=assignee_principal_id,
        job_kind=str(job.get("kind") or ""),
    )
    if not ok:
        raise PermissionError(reason)
    record = {
        "job_id": job_id,
        "org_id": org_id,
        "assignee_principal_id": assignee_principal_id,
        "assigned_by": assigned_by,
        "assigned_at": datetime.now(UTC).isoformat(),
        "claim_label": "asserted",
    }
    store.upsert_assignment(record)
    job = dict(job)
    job["assignee_principal_id"] = assignee_principal_id
    job["updated_at"] = datetime.now(UTC).isoformat()
    store.upsert_job(job)
    emit_mesh_event(
        store=store,
        org_id=org_id,
        event_type="mesh.assign",
        actor_principal_id=assigned_by,
        job_id=job_id,
        payload={"assignee": assignee_principal_id},
    )
    return record


def release_assignment(
    *,
    store: PlatformStore,
    job_id: str,
    org_id: str,
    actor_principal_id: str,
) -> None:
    store.delete_assignment(job_id)
    job = store.get_job(job_id)
    if job and job.get("org_id") == org_id:
        job = dict(job)
        job["assignee_principal_id"] = ""
        job["updated_at"] = datetime.now(UTC).isoformat()
        store.upsert_job(job)
    emit_mesh_event(
        store=store,
        org_id=org_id,
        event_type="mesh.release",
        actor_principal_id=actor_principal_id,
        job_id=job_id,
    )


def get_assignment(*, store: PlatformStore, job_id: str) -> dict[str, Any] | None:
    return store.get_assignment(job_id)
