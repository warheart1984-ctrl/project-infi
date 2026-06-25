from __future__ import annotations

from typing import Any

from nova.lineage.ucc_schema import UCCLineageEvent

_events: list[dict[str, Any]] = []
_structured: list[UCCLineageEvent] = []


def publish_lineage_event(event: UCCLineageEvent, *, extra: dict[str, Any] | None = None) -> None:
    payload = event.to_dict()
    if extra:
        payload["extra"].update(extra)
    _events.append(payload)
    _structured.append(event)


def list_lineage_events() -> list[dict[str, Any]]:
    return list(_events)


def list_structured_events() -> list[UCCLineageEvent]:
    return list(_structured)


def clear_lineage_bus() -> None:
    _events.clear()
    _structured.clear()
