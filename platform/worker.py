"""Platform job worker — Redis queue or inline poll."""

from __future__ import annotations

import time

from platform.adapters.dispatch import dispatch_job
from platform.auth.rbac import Principal
from platform.routing.region import worker_region
from platform.service import PlatformService
from platform.settings import PlatformSettings


def run_worker(*, once: bool = False) -> None:
    settings = PlatformSettings.from_env()
    svc = PlatformService(settings)
    poll = settings.worker_poll_seconds

    while True:
        region = worker_region()
        job_id = svc.queue.dequeue(timeout=1, region=region)
        if not job_id:
            pending = _pending_jobs(svc)
            for jid in pending:
                _process(svc, jid)
            time.sleep(poll)
            if once:
                return
            continue
        _process(svc, job_id)
        if once:
            return


def _pending_jobs(svc: PlatformService) -> list[str]:
    """When Redis is absent, process queued jobs from store."""
    if svc.settings.redis_url:
        return []
    ids: list[str] = []
    wr = worker_region()
    for org in _all_orgs(svc):
        for job in svc.store.list_jobs(org_id=org, status="queued"):
            if str(job.get("region") or "us").lower() == wr:
                ids.append(str(job["job_id"]))
    return ids


def _all_orgs(svc: PlatformService) -> list[str]:
    job = svc.store.get_job
    _ = job
    with svc.store._connect() as conn:
        rows = conn.execute("SELECT org_id FROM orgs").fetchall()
    return [str(r["org_id"]) for r in rows]


def _process(svc: PlatformService, job_id: str) -> None:
    job = svc.store.get_job(job_id)
    if not job or job.get("status") != "queued":
        return
    principal = Principal(
        principal_id=str(job.get("actor_principal_id") or "worker"),
        org_id=str(job.get("org_id")),
        roles=["operator"],
    )
    dispatch_job(
        registry=svc.jobs,
        artifact_index=svc.artifacts,
        principal=principal,
        job=job,
    )


if __name__ == "__main__":
    run_worker()
