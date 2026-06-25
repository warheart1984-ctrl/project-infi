"""Deterministic world replay — pure dict in/out."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _ensure_location(state: dict[str, Any], location: str) -> dict[str, Any]:
    locations = state.setdefault("locations", {})
    if location not in locations:
        locations[location] = {"flags": {}}
    entry = locations[location]
    flags = entry.get("flags")
    if not isinstance(flags, dict):
        flags = {}
        entry["flags"] = flags
    return entry


def apply_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    location = _ensure_location(state, event["location"])
    flags = location["flags"]
    action_type = event["action_type"]
    if action_type == "boss_defeated":
        flags["boss_defeated"] = True
        boss = event.get("action_payload", {}).get("boss")
        if boss:
            flags["boss_name"] = boss
    else:
        raise ValueError(f"unsupported action_type: {action_type}")


def replay_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    state: dict[str, Any] = {"locations": {}}
    ordered = sorted(events, key=lambda item: item["timestamp"])
    for event in ordered:
        apply_event(state, event)
    return deepcopy(state)
