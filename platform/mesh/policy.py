"""Org mesh policy (v22)."""

from __future__ import annotations

from typing import Any

from platform.store import PlatformStore


def get_mesh_policy(org: dict[str, Any] | None) -> dict[str, Any]:
    if not org:
        return {}
    return dict(org.get("mesh_policy") or {})


def set_mesh_policy(*, store: PlatformStore, org_id: str, policy: dict[str, Any]) -> dict[str, Any]:
    org = store.get_org(org_id) or {"org_id": org_id}
    org["mesh_policy"] = policy
    store.upsert_org(org)
    return policy


def count_assignments_for_operator(*, store: PlatformStore, org_id: str, principal_id: str) -> int:
    n = 0
    for job in store.list_jobs(org_id=org_id):
        if job.get("assignee_principal_id") == principal_id:
            n += 1
    return n


def evaluate_mesh_policy(
    *,
    store: PlatformStore,
    org_id: str,
    assignee_principal_id: str = "",
    job_kind: str = "",
) -> tuple[bool, str]:
    org = store.get_org(org_id)
    policy = get_mesh_policy(org)
    max_assign = int(policy.get("max_assignments_per_operator") or 0)
    if max_assign and assignee_principal_id:
        if count_assignments_for_operator(store=store, org_id=org_id, principal_id=assignee_principal_id) >= max_assign:
            return False, "max_assignments_per_operator exceeded"
    if policy.get("require_on_call_for_drift_investigation") and job_kind == "slingshot.launch":
        for job in store.list_jobs(org_id=org_id, subsystem="drift_detector"):
            if job.get("kind") == "drift_investigation" and job.get("status") not in {"complete", "cancelled"}:
                if not store.get_on_call(org_id):
                    return False, "on-call required for open drift_investigation"
    return True, "ok"
