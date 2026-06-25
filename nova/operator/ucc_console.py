from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from nova.lineage.ucc_schema import UCCLineageEvent


@dataclass
class UCCMetrics:
    avg_overload: float
    audhd_sessions: int
    linear_sessions: int
    mixed_sessions: int
    protection_triggers: int
    interpreter_usage_rate: float


class UCCOperatorConsole:
    def __init__(self, events: list[UCCLineageEvent], raw_events: list[dict[str, Any]] | None = None) -> None:
        self.events = events
        self.raw_events = raw_events or [event.to_dict() for event in events]

    def compute_metrics(self) -> UCCMetrics:
        if not self.events:
            return UCCMetrics(0.0, 0, 0, 0, 0, 0.0)

        overloads = [event.ucc.overload_score for event in self.events if event.ucc.overload_score is not None]
        avg_overload = sum(overloads) / len(overloads) if overloads else 0.0

        audhd_sessions = len(
            {event.actor_id for event in self.events if event.ucc.cognitive_style == "audhd"}
        )
        linear_sessions = len(
            {event.actor_id for event in self.events if event.ucc.cognitive_style == "linear"}
        )
        mixed_sessions = len(
            {event.actor_id for event in self.events if event.ucc.cognitive_style == "mixed"}
        )

        protection_triggers = sum(
            1
            for event in self.events
            if event.ucc.protection_flags and any(event.ucc.protection_flags.values())
        )

        interpreter_used = [event.ucc.interpreter_used for event in self.events]
        interpreter_usage_rate = sum(1 for used in interpreter_used if used) / len(interpreter_used)

        return UCCMetrics(
            avg_overload=avg_overload,
            audhd_sessions=audhd_sessions,
            linear_sessions=linear_sessions,
            mixed_sessions=mixed_sessions,
            protection_triggers=protection_triggers,
            interpreter_usage_rate=interpreter_usage_rate,
        )

    def capability_stats(self, capability: str) -> dict[str, Any]:
        relevant_events: list[UCCLineageEvent] = []
        relevant_raw: list[dict[str, Any]] = []
        for event, raw in zip(self.events, self.raw_events):
            extra = raw.get("extra", {})
            if extra.get("capability") == capability:
                relevant_events.append(event)
                relevant_raw.append(raw)

        if not relevant_events:
            return {}

        overloads = [
            event.ucc.overload_score
            for event in relevant_events
            if event.ucc.overload_score is not None
        ]
        avg_overload = sum(overloads) / len(overloads) if overloads else 0.0
        styles = Counter(
            event.ucc.cognitive_style for event in relevant_events if event.ucc.cognitive_style
        )
        blocked_overload = sum(
            1
            for raw in relevant_raw
            if raw.get("extra", {}).get("blocked_reason") == "overload"
        )
        blocked_pacing = sum(
            1
            for raw in relevant_raw
            if raw.get("extra", {}).get("blocked_reason") == "pacing"
        )

        return {
            "avg_overload": avg_overload,
            "by_cognitive_style": dict(styles),
            "count": len(relevant_events),
            "blocked_overload": blocked_overload,
            "blocked_pacing": blocked_pacing,
        }

    def to_json(self) -> dict[str, Any]:
        metrics = self.compute_metrics()
        return {
            "avg_overload": metrics.avg_overload,
            "audhd_sessions": metrics.audhd_sessions,
            "linear_sessions": metrics.linear_sessions,
            "mixed_sessions": metrics.mixed_sessions,
            "protection_triggers": metrics.protection_triggers,
            "interpreter_usage_rate": metrics.interpreter_usage_rate,
        }
