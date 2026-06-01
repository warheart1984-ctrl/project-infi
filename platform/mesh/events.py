"""Append-only mesh events."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.store import PlatformStore


def emit_mesh_event(
    *,
    store: PlatformStore,
    org_id: str,
    event_type: str,
    actor_principal_id: str,
    job_id: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "event_id": new_id("mevt"),
        "org_id": org_id,
        "type": event_type,
        "actor_principal_id": actor_principal_id,
        "job_id": job_id,
        "payload": payload or {},
        "created_at": datetime.now(UTC).isoformat(),
    }
    saved = store.append_mesh_event(record)
    from platform.ledger.hooks import ledger_mesh_event

    ledger_mesh_event(
        store=store,
        org_id=org_id,
        event_type=event_type,
        payload={"event_id": saved.get("event_id"), "job_id": job_id},
    )
    return saved
