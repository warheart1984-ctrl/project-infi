"""platform_job.v1 schema helpers."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import (
    JOB_VERSION,
    PROOF_REQUIRED_KINDS,
    ClaimLabel,
    JobPriority,
    JobStatus,
    ProofStatus,
    SlaClass,
    Subsystem,
    new_id,
)

JOB_TYPE_BY_KIND: dict[str, str] = {
    "mechanic.scan": "scan",
    "slingshot.preload": "preload",
    "slingshot.launch": "launch",
    "lab.session": "session",
    "ai_factory.build": "build",
    "forgekeeper.plan": "plan",
    "drift_check": "drift_check",
    "drift_investigation": "drift_investigation",
    "workflow_run": "workflow_run",
}


def build_job_record(
    *,
    org_id: str,
    subsystem: Subsystem,
    kind: str,
    actor_principal_id: str,
    subsystem_job_id: str = "",
    correlation_id: str = "",
    parent_job_id: str = "",
    status: JobStatus = "queued",
    claim_label: ClaimLabel = "asserted",
    links: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    job_id: str | None = None,
    job_type: str = "",
    priority: JobPriority = "normal",
    cost_estimate: float = 0.0,
    sla_class: SlaClass = "interactive",
    related_job_ids: list[str] | None = None,
    tenant_id: str = "",
    region: str = "us",
    proof_status: ProofStatus = "asserted",
    proof_required: bool | None = None,
    assignee_principal_id: str = "",
    mesh_channel: str = "ops",
    federation_id: str = "",
    attestation_quorum: int = 2,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    jid = job_id or new_id("job")
    needs_proof = proof_required if proof_required is not None else kind in PROOF_REQUIRED_KINDS
    return {
        "job_version": JOB_VERSION,
        "job_id": jid,
        "org_id": org_id,
        "tenant_id": tenant_id or org_id,
        "region": region,
        "correlation_id": correlation_id or jid,
        "parent_job_id": parent_job_id,
        "related_job_ids": related_job_ids or [],
        "subsystem": subsystem,
        "subsystem_job_id": subsystem_job_id or jid,
        "kind": kind,
        "job_type": job_type or JOB_TYPE_BY_KIND.get(kind, "generic"),
        "priority": priority,
        "cost_estimate": cost_estimate,
        "actual_cost": 0.0,
        "sla_class": sla_class,
        "status": status,
        "claim_label": claim_label,
        "proof_status": proof_status,
        "proof_required": needs_proof,
        "primary_hash": "",
        "secondary_hash": "",
        "proof_consensus": "",
        "runtime_ms": 0,
        "tokens_used": 0,
        "created_at": now,
        "updated_at": now,
        "actor_principal_id": actor_principal_id,
        "assignee_principal_id": assignee_principal_id,
        "mesh_channel": mesh_channel,
        "federation_id": federation_id or jid,
        "attestation_quorum": attestation_quorum,
        "links": links or [],
        "metadata": metadata or {},
    }


def validate_job_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "job_version",
        "job_id",
        "org_id",
        "subsystem",
        "kind",
        "status",
    ):
        if not payload.get(field):
            errors.append(f"missing:{field}")
    if payload.get("job_version") != JOB_VERSION:
        errors.append("invalid:job_version")
    return errors


def add_related_job(job: dict[str, Any], related_id: str) -> dict[str, Any]:
    job = dict(job)
    related = list(job.get("related_job_ids") or [])
    if related_id and related_id not in related:
        related.append(related_id)
    job["related_job_ids"] = related
    job["updated_at"] = datetime.now(UTC).isoformat()
    return job


def update_job_status(
    job: dict[str, Any],
    *,
    status: JobStatus,
    claim_label: ClaimLabel | None = None,
    subsystem_job_id: str | None = None,
    links: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    proof_status: ProofStatus | None = None,
    primary_hash: str | None = None,
    secondary_hash: str | None = None,
    runtime_ms: int | None = None,
    actual_cost: float | None = None,
) -> dict[str, Any]:
    job = dict(job)
    started = job.get("_started_monotonic")
    job["status"] = status
    job["updated_at"] = datetime.now(UTC).isoformat()
    if claim_label:
        job["claim_label"] = claim_label
    if subsystem_job_id:
        job["subsystem_job_id"] = subsystem_job_id
    if links is not None:
        job["links"] = links
    if metadata is not None:
        merged = dict(job.get("metadata") or {})
        merged.update(metadata)
        job["metadata"] = merged
    if proof_status:
        job["proof_status"] = proof_status
    if primary_hash is not None:
        job["primary_hash"] = primary_hash
    if secondary_hash is not None:
        job["secondary_hash"] = secondary_hash
    if runtime_ms is not None:
        job["runtime_ms"] = runtime_ms
    elif started and status in {"complete", "failed", "cancelled"}:
        job["runtime_ms"] = int((time.monotonic() - float(started)) * 1000)
    if actual_cost is not None:
        job["actual_cost"] = actual_cost
    return job


def mark_job_started(job: dict[str, Any]) -> dict[str, Any]:
    job = dict(job)
    job["_started_monotonic"] = time.monotonic()
    return job
