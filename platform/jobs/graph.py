"""Build job relationship graphs."""

from __future__ import annotations

from typing import Any

from platform.store import PlatformStore


def build_job_graph(*, store: PlatformStore, job_id: str, org_id: str) -> dict[str, Any]:
    root = store.get_job(job_id)
    if not root:
        return {"job_id": job_id, "nodes": [], "edges": []}
    if root.get("org_id") != org_id:
        return {"job_id": job_id, "nodes": [], "edges": []}

    nodes: dict[str, dict[str, Any]] = {job_id: _node(root)}
    edges: list[dict[str, str]] = []
    frontier = [job_id]
    seen = {job_id}

    while frontier:
        current_id = frontier.pop(0)
        current = store.get_job(current_id)
        if not current:
            continue
        corr = str(current.get("correlation_id") or "")
        candidates = store.list_jobs(org_id=org_id, correlation_id=corr) if corr else []
        for rel_id in current.get("related_job_ids") or []:
            other = store.get_job(str(rel_id))
            if other:
                candidates.append(other)
        parent = str(current.get("parent_job_id") or "")
        if parent:
            pjob = store.get_job(parent)
            if pjob:
                candidates.append(pjob)
                edges.append({"from": parent, "to": current_id, "type": "parent"})
        for child in store.list_jobs(org_id=org_id):
            if str(child.get("parent_job_id") or "") == current_id:
                candidates.append(child)
                edges.append({"from": current_id, "to": str(child["job_id"]), "type": "parent"})

        for job in candidates:
            jid = str(job.get("job_id"))
            if jid in seen or job.get("org_id") != org_id:
                continue
            seen.add(jid)
            nodes[jid] = _node(job)
            frontier.append(jid)
            if str(job.get("parent_job_id") or "") == current_id:
                edges.append({"from": current_id, "to": jid, "type": "parent"})
            elif current_id in (job.get("related_job_ids") or []):
                edges.append({"from": jid, "to": current_id, "type": "related"})
            else:
                edges.append({"from": current_id, "to": jid, "type": "correlation"})

    return {
        "job_id": job_id,
        "correlation_id": root.get("correlation_id"),
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def _node(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job.get("job_id"),
        "subsystem": job.get("subsystem"),
        "kind": job.get("kind"),
        "job_type": job.get("job_type"),
        "status": job.get("status"),
        "proof_status": job.get("proof_status", "asserted"),
        "subsystem_job_id": job.get("subsystem_job_id"),
    }
