"""Canonical serialization and hashing for world events."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.cori.world.models import WorldEventRecord


def event_canonical(event: WorldEventRecord) -> dict[str, Any]:
    ts = event.timestamp
    if ts.tzinfo is not None:
        timestamp = ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        timestamp = ts.replace(microsecond=0).isoformat() + "Z"
    return {
        "id": event.id,
        "actor_id": event.actor_id,
        "action_type": event.action_type,
        "action_payload": event.action_payload,
        "location": event.location,
        "timestamp": timestamp,
    }


def compute_event_hash(event: WorldEventRecord) -> str:
    serialized = json.dumps(event_canonical(event), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
