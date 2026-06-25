"""Pluggable external feed sources for the realtime event-cause predictor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from typing import Any, Callable, Iterator
import json
import os
from pathlib import Path


@dataclass
class RealtimeFeedEvent:
    source: str
    event_type: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


FeedSource = Callable[[], Iterator[RealtimeFeedEvent]]


def _wrap_ul(payload: dict[str, Any]) -> dict[str, Any]:
    from src.aais_ul.runtime import attach_ul_substrate

    return attach_ul_substrate(dict(payload))


class RealtimeFeedAdapter:
    """Collect governed feed events from configured sources."""

    def __init__(self) -> None:
        self._sources: list[FeedSource] = []
        self._register_default_sources()

    def _register_default_sources(self) -> None:
        self._sources.append(self._seam_log_source)
        feed_path = os.getenv("AAIS_REALTIME_FEED_FILE", "").strip()
        if feed_path:
            self._sources.append(lambda: self._file_tail_source(Path(feed_path)))

    def _seam_log_source(self) -> Iterator[RealtimeFeedEvent]:
        try:
            from src.seam_log import list_seam_events

            for event in list_seam_events(limit=8) or []:
                yield RealtimeFeedEvent(
                    source="seam_log",
                    event_type=str(event.get("classification") or "seam"),
                    payload=dict(event),
                )
        except Exception:
            return
        return

    def _file_tail_source(self, path: Path) -> Iterator[RealtimeFeedEvent]:
        if not path.is_file():
            return
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
        except OSError:
            return
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                payload = {"raw": line}
            yield RealtimeFeedEvent(
                source="file_tail",
                event_type=str(payload.get("type") or "feed_line"),
                payload=payload,
            )

    def collect(self, *, limit: int = 16) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for source in self._sources:
            for event in source():
                events.append(
                    _wrap_ul(
                        {
                            "source": event.source,
                            "event_type": event.event_type,
                            "timestamp": event.timestamp,
                            "payload": event.payload,
                        }
                    )
                )
                if len(events) >= limit:
                    return events
        return events


_default_adapter: RealtimeFeedAdapter | None = None


def get_realtime_feed_adapter() -> RealtimeFeedAdapter:
    global _default_adapter
    if _default_adapter is None:
        _default_adapter = RealtimeFeedAdapter()
    return _default_adapter
