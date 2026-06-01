"""Assignment queue (v38)."""

from __future__ import annotations

from typing import Any

from platform.store import PlatformStore


def get_assignment_queue(org: dict[str, Any] | None) -> list[str]:
    if not org:
        return []
    return list(org.get("assignment_queue") or [])


def set_assignment_queue(*, store: PlatformStore, org_id: str, principal_ids: list[str]) -> list[str]:
    org = store.get_org(org_id) or {"org_id": org_id}
    org["assignment_queue"] = principal_ids
    store.upsert_org(org)
    return principal_ids


def dequeue_assignee(*, store: PlatformStore, org_id: str) -> str:
    org = store.get_org(org_id) or {}
    queue = list(org.get("assignment_queue") or [])
    if not queue:
        return ""
    nxt = queue.pop(0)
    queue.append(nxt)
    org["assignment_queue"] = queue
    store.upsert_org(org)
    return nxt
