"""Ingest world events into memory records."""

from __future__ import annotations

from src.cori.world.canonical import compute_event_hash, event_canonical
from src.cori.world.models import WorldEventRecord, WorldMemoryRecord


def register_world_event(event: WorldEventRecord) -> WorldMemoryRecord:
    """world_register.py: Event → WorldMemoryRecord with event_hash and raw."""
    raw = event_canonical(event)
    return WorldMemoryRecord(
        event_id=event.id,
        event_hash=compute_event_hash(event),
        raw=raw,
    )
