"""On-call rotation resolution."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore


def set_on_call_schedule(
    *,
    store: PlatformStore,
    org_id: str,
    principal_ids: list[str],
    rotation_id: str = "",
    effective_from: str = "",
    effective_to: str = "",
) -> dict[str, Any]:
    rid = rotation_id or f"{org_id}:oncall"
    payload = {
        "rotation_id": rid,
        "org_id": org_id,
        "principal_ids": principal_ids,
        "effective_from": effective_from or datetime.now(UTC).isoformat(),
        "effective_to": effective_to,
    }
    return store.upsert_on_call(payload)


def current_on_call(*, store: PlatformStore, org_id: str) -> str | None:
    sched = store.get_on_call(org_id)
    if not sched:
        return None
    ids = sched.get("principal_ids") or []
    if not ids:
        return None
    return str(ids[0])
