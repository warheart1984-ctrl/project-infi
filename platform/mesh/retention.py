"""Mesh event retention (v37)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from src.datetime_compat import UTC

from platform.mesh.policy import get_mesh_policy
from platform.store import PlatformStore


def compact_org_mesh_events(*, store: PlatformStore, org_id: str) -> int:
    org = store.get_org(org_id) or {}
    policy = get_mesh_policy(org)
    days = int(policy.get("event_retention_days") or 30)
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    return store.compact_mesh_events(org_id=org_id, before_iso=cutoff)
