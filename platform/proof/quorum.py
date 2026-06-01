"""k-of-n proof quorum promotion (v20+)."""

from __future__ import annotations

import os
from typing import Any, Callable

from platform.proof.federation import federation_status
from platform.proof.runner import promote_consensus
from platform.proof.witnesses import witness_policy_satisfied
from platform.store import PlatformStore


def proof_quorum() -> int:
    return int(os.environ.get("PLATFORM_PROOF_QUORUM", "2"))


def _spawn_dispute_drift(
    *,
    store: PlatformStore,
    job: dict[str, Any],
    enqueue: Callable[..., bool] | None,
) -> None:
    if not enqueue:
        return
    from platform.drift.scheduler import maybe_enqueue_investigation

    maybe_enqueue_investigation(
        store=store,
        org_id=str(job["org_id"]),
        drift_job=job,
        violation_class="II",
        enqueue=enqueue,
    )


def evaluate_quorum(
    *,
    store: PlatformStore,
    job: dict[str, Any],
    enqueue: Callable[..., bool] | None = None,
) -> tuple[dict[str, Any], bool]:
    job_id = str(job.get("job_id"))
    job = dict(store.get_job(job_id) or job)
    status = federation_status(store=store, job=job)
    if status.get("hash_mismatch"):
        job = dict(job)
        job["proof_status"] = "disputed"
        job["claim_label"] = "asserted"
        store.upsert_job(job)
        _spawn_dispute_drift(store=store, job=job, enqueue=enqueue)
        return job, False
    if not status["quorum_met"]:
        return job, False
    if not witness_policy_satisfied(store=store, job_id=job_id):
        return job, False
    h = ""
    for a in status["attestations"]:
        h = str(a.get("result_hash") or "")
        break
    updated = promote_consensus(job=job, primary_hash=h, secondary_hash=h)
    store.upsert_job(updated)
    return updated, True


def federation_blocks_workflow_step(*, store: PlatformStore, job: dict[str, Any], next_kind: str) -> tuple[bool, str]:
    from platform.common import PROOF_REQUIRED_KINDS

    if next_kind not in PROOF_REQUIRED_KINDS:
        return True, "ok"
    parent_id = str(job.get("parent_job_id") or job.get("job_id"))
    parent = store.get_job(parent_id) or job
    if parent.get("proof_status") == "proven":
        return True, "ok"
    if not parent.get("proof_required"):
        return True, "ok"
    status = federation_status(store=store, job=parent)
    if not status["quorum_met"]:
        return False, "proof federation quorum not met for workflow step"
    parent_id = str(parent.get("job_id"))
    if not witness_policy_satisfied(store=store, job_id=parent_id):
        return False, "witness policy not satisfied for workflow step"
    return True, "ok"
