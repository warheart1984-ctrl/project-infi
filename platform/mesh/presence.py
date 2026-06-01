"""Operator presence heartbeats."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.store import PlatformStore


def heartbeat_presence(
    *,
    store: PlatformStore,
    org_id: str,
    principal_id: str,
    status: str = "online",
    session_id: str = "",
) -> dict[str, Any]:
    payload = {
        "org_id": org_id,
        "principal_id": principal_id,
        "status": status,
        "last_seen": datetime.now(UTC).isoformat(),
        "session_id": session_id,
    }
    return store.upsert_presence(payload)


def list_online_operators(
    *,
    store: PlatformStore,
    org_id: str,
    max_age_seconds: int = 300,
) -> list[dict[str, Any]]:
    return store.list_presence(org_id=org_id, max_age_seconds=max_age_seconds)
