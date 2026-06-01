"""Sentinel adapter protocol."""

from __future__ import annotations

from typing import Protocol

from scorpion.events import TraceEvent


class SentinelAdapter(Protocol):
    adapter_id: str

    def ingest(self, trace_path: str) -> list[TraceEvent]:
        ...

    def describe(self, trace_path: str) -> dict:
        ...
