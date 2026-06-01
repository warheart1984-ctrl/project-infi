"""Enqueue drift_check / drift_investigation jobs."""

from __future__ import annotations

from typing import Any

from platform.common import new_id
from platform.jobs.schema import build_job_record
from platform.store import PlatformStore


def maybe_enqueue_drift(
    *,
    store: PlatformStore,
    org_id: str,
    source_job_id: str,
    findings: list[dict[str, Any]],
    enqueue: Any,
) -> dict[str, Any] | None:
    if not findings:
        return None
    max_sev = max(int(f.get("severity", 0)) for f in findings)
    if max_sev < 1:
        return None
    job = build_job_record(
        org_id=org_id,
        subsystem="drift_detector",
        kind="drift_check",
        actor_principal_id="platform-drift",
        parent_job_id=source_job_id,
        related_job_ids=[source_job_id],
        metadata={"findings": findings, "source_job_id": source_job_id},
        job_type="drift_check",
    )
    store.upsert_job(job)
    enqueue(str(job["job_id"]), region=str(job.get("region") or "us"))
    return job


def maybe_enqueue_investigation(
    *,
    store: PlatformStore,
    org_id: str,
    drift_job: dict[str, Any],
    violation_class: str,
    enqueue: Any,
) -> dict[str, Any] | None:
    if violation_class not in {"II", "III", "class_ii", "class_iii"}:
        return None
    job = build_job_record(
        org_id=org_id,
        subsystem="drift_detector",
        kind="drift_investigation",
        actor_principal_id="platform-drift",
        parent_job_id=str(drift_job.get("job_id")),
        related_job_ids=[str(drift_job.get("job_id"))],
        metadata={"violation_class": violation_class},
        job_type="drift_investigation",
    )
    store.upsert_job(job)
    enqueue(str(job["job_id"]), region=str(job.get("region") or "us"))
    return job
