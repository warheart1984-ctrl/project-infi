"""Deterministic replay of world events into state."""

from __future__ import annotations

from src.cori.world.models import WorldEventRecord, WorldState


def _ensure_location(state: WorldState, location: str) -> dict[str, object]:
    if location not in state.locations:
        state.locations[location] = {"flags": {}}
    flags = state.locations[location].get("flags")
    if not isinstance(flags, dict):
        flags = {}
        state.locations[location]["flags"] = flags
    return state.locations[location]


def apply_event(state: WorldState, event: WorldEventRecord) -> None:
    location = _ensure_location(state, event.location)
    flags = location["flags"]
    assert isinstance(flags, dict)

    if event.action_type == "boss_defeated":
        flags["boss_defeated"] = True
        boss = event.action_payload.get("boss")
        if boss:
            flags["boss_name"] = boss
    else:
        raise ValueError(f"unsupported action_type: {event.action_type}")


def replay_world(events: list[WorldEventRecord]) -> WorldState:
    """Replay events in timestamp order to produce a WorldState."""
    state = WorldState()
    ordered = sorted(events, key=lambda event: event.timestamp)
    for event in ordered:
        apply_event(state, event)
    return state
