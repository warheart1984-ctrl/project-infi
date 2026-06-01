"""Autonomous org mesh autopilot (v41–v42) — policy-bound routing only."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.mesh.assignment import assign_job
from platform.mesh.on_call import current_on_call
from platform.mesh.policy import evaluate_mesh_policy
from platform.mesh.queue import dequeue_assignee, get_assignment_queue
from platform.store import PlatformStore


def get_routing_policy(org: dict[str, Any] | None) -> dict[str, Any]:
    if not org:
        return {}
    return dict(org.get("routing_policy") or {})


def set_routing_policy(*, store: PlatformStore, org_id: str, policy: dict[str, Any]) -> dict[str, Any]:
    org = store.get_org(org_id) or {"org_id": org_id}
    org["routing_policy"] = policy
    store.upsert_org(org)
    return policy


def run_autopilot(
    *,
    store: PlatformStore,
    org_id: str,
    mode: str = "dry_run",
    actor_principal_id: str = "autopilot",
) -> dict[str, Any]:
    org = store.get_org(org_id) or {}
    policy = get_routing_policy(org)
    actions: list[dict[str, Any]] = []
    max_n = int(policy.get("max_auto_assignments_per_run") or 5)
    assigned = 0

    if policy.get("auto_assign_from_queue") and get_assignment_queue(org):
        for job in store.list_jobs(org_id=org_id):
            if assigned >= max_n:
                break
            if job.get("assignee_principal_id"):
                continue
            if job.get("status") in {"complete", "cancelled"}:
                continue
            assignee = dequeue_assignee(store=store, org_id=org_id)
            if not assignee:
                break
            action = {
                "type": "assign",
                "job_id": job["job_id"],
                "assignee": assignee,
            }
            ok, reason = evaluate_mesh_policy(
                store=store,
                org_id=org_id,
                assignee_principal_id=assignee,
                job_kind=str(job.get("kind") or ""),
            )
            action["policy_ok"] = ok
            if not ok:
                action["policy_error"] = reason
            if mode == "apply" and ok:
                try:
                    assign_job(
                        store=store,
                        job_id=str(job["job_id"]),
                        org_id=org_id,
                        assignee_principal_id=assignee,
                        assigned_by=actor_principal_id,
                    )
                    action["applied"] = True
                except PermissionError as exc:
                    action["applied"] = False
                    action["error"] = str(exc)
            actions.append(action)
            assigned += 1

    if policy.get("suggest_on_call_on_drift"):
        for job in store.list_jobs(org_id=org_id, subsystem="drift_detector"):
            if job.get("status") not in {"complete", "cancelled"}:
                on_call = current_on_call(store=store, org_id=org_id)
                actions.append(
                    {
                        "type": "suggest_on_call",
                        "drift_job_id": job.get("job_id"),
                        "on_call_principal": on_call,
                    }
                )

    receipt = {
        "run_id": new_id("auto"),
        "org_id": org_id,
        "mode": mode,
        "actions": actions,
        "created_at": datetime.now(UTC).isoformat(),
        "claim_label": "asserted",
    }
    store.append_autopilot_run(receipt)
    return receipt
