from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable
import time
from uuid import uuid4

from fastapi import APIRouter, Query

from nova.node.feature_manifest import feature_manifest
from nova.node.ledger import append_jsonl, read_jsonl, runtime_dir
from nova.node.substrate_events import (
    append_substrate_event,
    legacy_event_to_substrate,
    remember_trace_event,
)


DEFAULT_CHANNELS = ["governance.*", "test.*", "git.*", "tool.*", "replay.*", "node.*", "substrate.*"]
DEFAULT_MAX_EVENTS = 5000

router = APIRouter()


@dataclass(frozen=True)
class Event:
    id: str
    channel: str
    type: str
    payload: dict[str, Any]
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Event":
        return cls(
            id=str(payload.get("id") or ""),
            channel=str(payload.get("channel") or ""),
            type=str(payload.get("type") or ""),
            payload=dict(payload.get("payload") or {}),
            timestamp=float(payload.get("timestamp") or 0),
        )


class EventBus:
    def __init__(
        self,
        channels: list[str] | None = None,
        max_events: int = DEFAULT_MAX_EVENTS,
        *,
        persist: bool = True,
        path: Path | None = None,
    ) -> None:
        self.channels = list(channels or DEFAULT_CHANNELS)
        self.max_events = max_events
        self.persist = persist
        self.path = path or event_log_path()
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self._history = self._load_history()

    def subscribe(self, pattern: str, handler: Callable[[Event], None]) -> None:
        self._subscribers.setdefault(pattern, []).append(handler)

    def emit(self, channel: str, type_: str, payload: dict[str, Any] | None = None) -> Event:
        if not self._allowed_channel(channel):
            raise ValueError(f"unsupported event channel: {channel}")
        event = Event(
            id=str(uuid4()),
            channel=channel,
            type=type_,
            payload=payload or {},
            timestamp=time.time(),
        )
        self._append_history(event)
        if self.persist:
            append_jsonl(self.path, event.to_dict())
            substrate_event = legacy_event_to_substrate(event)
            if substrate_event is not None:
                written = append_substrate_event(substrate_event)
                remember_trace_event(written)
        self._dispatch(event)
        return event

    def history(self, channel_prefix: str | None = None, *, limit: int | None = None) -> list[Event]:
        events = list(self._history)
        if channel_prefix:
            events = [event for event in events if event.channel.startswith(channel_prefix)]
        if limit is not None:
            events = events[-limit:]
        return events

    def _append_history(self, event: Event) -> None:
        self._history.append(event)
        if len(self._history) > self.max_events:
            self._history = self._history[-self.max_events :]

    def _dispatch(self, event: Event) -> None:
        for pattern, handlers in self._subscribers.items():
            if _matches(pattern, event.channel):
                for handler in handlers:
                    handler(event)

    def _allowed_channel(self, channel: str) -> bool:
        return any(_matches(pattern, channel) for pattern in self.channels)

    def _load_history(self) -> list[Event]:
        if not self.persist:
            return []
        events: list[Event] = []
        for entry in read_jsonl(self.path):
            try:
                event = Event.from_dict(entry)
            except (TypeError, ValueError):
                continue
            if event.channel and self._allowed_channel(event.channel):
                events.append(event)
        return events[-self.max_events :]


def event_log_path() -> Path:
    return runtime_dir() / "event-bus.jsonl"


def read_event_history(channel_prefix: str | None = None, *, limit: int | None = None) -> list[dict[str, Any]]:
    events = [Event.from_dict(entry) for entry in read_jsonl(event_log_path())]
    if channel_prefix:
        events = [event for event in events if event.channel.startswith(channel_prefix)]
    if limit is not None:
        events = events[-limit:]
    return [event.to_dict() for event in events]


_BUS_CACHE: dict[tuple[str, int], EventBus] = {}


def get_event_bus(*, max_events: int = DEFAULT_MAX_EVENTS) -> EventBus:
    path = event_log_path()
    key = (str(path.resolve()), max_events)
    bus = _BUS_CACHE.get(key)
    if bus is None:
        bus = EventBus(max_events=max_events, path=path)
        _BUS_CACHE[key] = bus
    return bus


def reset_event_bus() -> None:
    _BUS_CACHE.clear()


@router.get("/node/events")
async def get_node_events(
    prefix: str | None = None,
    limit: int = Query(default=500, ge=1, le=5000),
) -> dict[str, Any]:
    return {
        "channels": DEFAULT_CHANNELS,
        "events": read_event_history(prefix, limit=limit),
    }


@router.get("/node/feature-manifest")
async def get_feature_manifest() -> dict[str, Any]:
    return {"manifest": feature_manifest()}


def _matches(pattern: str, channel: str) -> bool:
    if pattern.endswith(".*"):
        return channel.startswith(pattern[:-1])
    return pattern == channel
