"""Fixture-based Sentinel adapter (Stage 1)."""

from __future__ import annotations

from scorpion.events import TraceEvent, load_events_from_path


class FixtureSentinel:
    adapter_id = "fixture-sentinel.v1"

    def ingest(self, trace_path: str) -> list[TraceEvent]:
        return load_events_from_path(trace_path)

    def describe(self, trace_path: str) -> dict:
        events = self.ingest(trace_path)
        domains = sorted({e.domain for e in events})
        return {
            "adapter_id": self.adapter_id,
            "trace_path": trace_path,
            "event_count": len(events),
            "domains": domains,
            "claim_label": "proven",
        }
