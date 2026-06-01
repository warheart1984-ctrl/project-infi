"""Normalized trace event types for Scorpion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EVENT_SCHEMA = "scorpion.event.v1"
VALID_DOMAINS = frozenset(
    {
        "syscall_sequence",
        "scheduler_rhythm",
        "memory_lifecycle",
        "fd_flow",
        "ipc_choreography",
        "privilege_transition",
        "entropy_signature",
        "timing_delta",
    }
)


@dataclass(slots=True)
class TraceEvent:
    ts_ns: int
    domain: str
    actor: str
    payload: dict[str, Any] = field(default_factory=dict)
    lineage_id: str = ""

    def normalized(self) -> dict[str, Any]:
        domain = self.domain.strip()
        if domain not in VALID_DOMAINS:
            raise ValueError(f"invalid event domain: {domain}")
        return {
            "schema": EVENT_SCHEMA,
            "ts_ns": int(self.ts_ns),
            "domain": domain,
            "actor": self.actor.strip() or "unknown",
            "payload": dict(self.payload),
            "lineage_id": self.lineage_id.strip(),
        }

    def model_dump(self) -> dict[str, Any]:
        return self.normalized()


def parse_event_line(line: str) -> TraceEvent:
    import json

    raw = json.loads(line)
    return TraceEvent(
        ts_ns=int(raw.get("ts_ns") or 0),
        domain=str(raw.get("domain") or ""),
        actor=str(raw.get("actor") or ""),
        payload=dict(raw.get("payload") or {}),
        lineage_id=str(raw.get("lineage_id") or ""),
    )


def load_events_from_path(path: str) -> list[TraceEvent]:
    from pathlib import Path

    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"trace not found: {target}")
    events: list[TraceEvent] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        events.append(parse_event_line(stripped))
    return sorted(events, key=lambda e: (e.ts_ns, e.domain, e.actor))
