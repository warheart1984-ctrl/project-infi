"""Bone King demo event factory."""

from __future__ import annotations

from datetime import UTC, datetime

from src.cori.world.models import WorldEventRecord


def bone_king_defeated_event() -> WorldEventRecord:
    return WorldEventRecord(
        id="EVT-1",
        actor_id="PLAYER-1",
        action_type="boss_defeated",
        action_payload={"boss": "Bone King"},
        location="Forgotten Crypt",
        timestamp=datetime(2026, 6, 22, 20, 0, 0, tzinfo=UTC),
    )
