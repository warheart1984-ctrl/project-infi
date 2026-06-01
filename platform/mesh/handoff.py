"""Shift handoff bundles."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.mesh.events import emit_mesh_event
from platform.store import PlatformStore


def create_handoff_bundle(
    *,
    store: PlatformStore,
    org_id: str,
    from_principal_id: str,
    to_principal_id: str,
    notes: str = "",
    runbook_ref: str = "",
) -> dict[str, Any]:
    open_jobs: list[str] = []
    drift_jobs: list[str] = []
    for job in store.list_jobs(org_id=org_id):
        if job.get("assignee_principal_id") == from_principal_id and job.get("status") in {"queued", "running"}:
            open_jobs.append(str(job["job_id"]))
        if job.get("subsystem") == "drift_detector" and job.get("status") not in {"complete", "cancelled"}:
            drift_jobs.append(str(job["job_id"]))
    bundle = {
        "bundle_id": new_id("handoff"),
        "org_id": org_id,
        "from_principal": from_principal_id,
        "to_principal": to_principal_id,
        "open_job_ids": open_jobs,
        "drift_job_ids": drift_jobs,
        "notes": notes,
        "runbook_ref": runbook_ref or "docs/subsystems/platform/OPERATIONAL_RUNBOOK.md",
        "created_at": datetime.now(UTC).isoformat(),
    }
    store.upsert_handoff(bundle)
    emit_mesh_event(
        store=store,
        org_id=org_id,
        event_type="mesh.handoff",
        actor_principal_id=from_principal_id,
        payload={"bundle_id": bundle["bundle_id"], "to": to_principal_id},
    )
    return bundle
