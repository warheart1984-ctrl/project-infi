"""Platform job CRUD and dispatch."""

from __future__ import annotations

from typing import Any

from platform.auth.audit import append_audit_event
from platform.auth.rbac import Principal
from platform.jobs.queue import JobQueue
from platform.billing.aggregator import record_job_completion
from platform.jobs.schema import add_related_job, build_job_record, update_job_status
from platform.billing.engine import evaluate_billing_gate
from platform.policy.engine import (
    drift_blocks_slingshot,
    evaluate_admission,
    evaluate_dsl_admission,
    mesh_blocks_slingshot,
)
from platform.routing.region import enqueue_job_for_region, resolve_job_region
from platform.store import PlatformStore


class JobRegistry:
    def __init__(
        self,
        *,
        store: PlatformStore,
        queue: JobQueue | None = None,
        audit_path: Any = None,
        quota_limiter: Any = None,
    ) -> None:
        self.store = store
        self.queue = queue or JobQueue("")
        self.audit_path = audit_path
        self.quota_limiter = quota_limiter

    def _audit(self, *, principal: Principal, action: str, job: dict[str, Any]) -> None:
        if self.audit_path is None:
            return
        from pathlib import Path

        append_audit_event(
            audit_path=Path(self.audit_path),
            org_id=principal.org_id,
            principal_id=principal.principal_id,
            action=action,
            job_id=str(job.get("job_id", "")),
            details={"subsystem": job.get("subsystem"), "kind": job.get("kind")},
            store=self.store,
        )
        self.store.append_audit_row(
            {
                "org_id": principal.org_id,
                "principal_id": principal.principal_id,
                "action": action,
                "job_id": job.get("job_id"),
            }
        )

    def create_job(
        self,
        *,
        principal: Principal,
        subsystem: str,
        kind: str,
        params: dict[str, Any] | None = None,
        subsystem_job_id: str = "",
        correlation_id: str = "",
        parent_job_id: str = "",
        priority: str = "normal",
        cost_estimate: float = 0.0,
        sla_class: str = "interactive",
    ) -> dict[str, Any]:
        org = self.store.get_org(principal.org_id)
        running = len([j for j in self.store.list_jobs(org_id=principal.org_id) if j.get("status") in {"queued", "running"}])
        today = len(self.store.list_jobs(org_id=principal.org_id))
        job_req = {
            "subsystem": subsystem,
            "kind": kind,
            "job_type": kind.split(".")[-1],
            "cost_estimate": cost_estimate,
        }
        ok, reason = evaluate_admission(
            org=org,
            job_request=job_req,
            running_jobs=running,
            jobs_today=today,
        )
        if not ok:
            raise PermissionError(reason)
        bok, breason = evaluate_billing_gate(org)
        if not bok:
            raise PermissionError(breason)
        if kind == "slingshot.launch":
            dok, dreason = drift_blocks_slingshot(store=self.store, org_id=principal.org_id)
            if not dok:
                raise PermissionError(dreason)
            mok, mreason = mesh_blocks_slingshot(
                store=self.store,
                org_id=principal.org_id,
                job_request=job_req,
            )
            if not mok:
                raise PermissionError(mreason)
        dsl_ok, dsl_reason = evaluate_dsl_admission(
            store=self.store,
            org=org,
            job_request=job_req,
            principal_role=str((principal.roles or ["operator"])[0]),
        )
        if not dsl_ok:
            raise PermissionError(dsl_reason)
        if self.quota_limiter:
            qok, _ = self.quota_limiter.check_job_submit(org_id=principal.org_id, org=org)
            if not qok:
                raise PermissionError("daily job quota exceeded")
        related: list[str] = []
        if parent_job_id:
            related.append(parent_job_id)
        region = resolve_job_region(org=org, requested=str(org.get("region") if org else "us"))
        job = build_job_record(
            org_id=principal.org_id,
            subsystem=subsystem,  # type: ignore[arg-type]
            kind=kind,
            actor_principal_id=principal.principal_id,
            subsystem_job_id=subsystem_job_id,
            correlation_id=correlation_id,
            parent_job_id=parent_job_id,
            related_job_ids=related,
            priority=priority,  # type: ignore[arg-type]
            cost_estimate=cost_estimate,
            sla_class=sla_class,  # type: ignore[arg-type]
            region=region,
            metadata={"params": params or {}},
        )
        if parent_job_id:
            parent = self.store.get_job(parent_job_id)
            if parent:
                self.store.upsert_job(add_related_job(parent, str(job["job_id"])))
        self.store.upsert_job(job)
        self._audit(principal=principal, action="job.create", job=job)
        enqueue_job_for_region(queue=self.queue, job_id=str(job["job_id"]), region=region)
        return job

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.store.get_job(job_id)

    def list_jobs(
        self,
        *,
        org_id: str,
        subsystem: str = "",
        status: str = "",
        correlation_id: str = "",
        job_type: str = "",
        proof_status: str = "",
    ) -> list[dict[str, Any]]:
        return self.store.list_jobs(
            org_id=org_id,
            subsystem=subsystem,
            status=status,
            correlation_id=correlation_id,
            job_type=job_type,
            proof_status=proof_status,
        )

    def save_job(self, job: dict[str, Any]) -> dict[str, Any]:
        self.store.upsert_job(job)
        if job.get("status") == "complete":
            record_job_completion(store=self.store, job=job)
        return job

    def cancel_job(self, *, principal: Principal, job_id: str) -> dict[str, Any] | None:
        job = self.store.get_job(job_id)
        if not job or job.get("org_id") != principal.org_id:
            if not principal.is_platform_admin():
                return None
        if job.get("status") in {"complete", "failed", "cancelled"}:
            return job
        updated = update_job_status(job, status="cancelled")
        self.store.upsert_job(updated)
        self._audit(principal=principal, action="job.cancel", job=updated)
        return updated
