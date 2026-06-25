"""TraceStore — append-only persistence for orchestrator traces."""

# Mythic: Trace Store
# Engineering: TraceStore
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from src.aaes_os.models import TraceEvent
from src.aaes_os.pipeline_types import AAESExecuteResult, AAESStep
from src.aaes_os.trace_bus import TraceBusValidator


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        row = asdict(value)
        for key, item in list(row.items()):
            if hasattr(item, "value"):
                row[key] = item.value
        return row
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "as_dict"):
        return value.as_dict()
    return value


class TraceStore:
    """In-memory index with optional JSONL append."""

    def __init__(self, *, path: Path | str | None = None) -> None:
        self._lock = Lock()
        self._records: dict[str, dict[str, Any]] = {}
        self._path = Path(path) if path else None
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

    def save_execute_result(
        self,
        result: AAESExecuteResult,
        *,
        bus: TraceBusValidator | None = None,
    ) -> None:
        if not isinstance(result, AAESExecuteResult):
            raise TypeError("result must be AAESExecuteResult")
        events: list[dict[str, Any]] = []
        if bus is not None:
            events = [row.as_dict() for row in bus.events_for_span(result.span_id)]
        record = {
            "trace_id": result.trace_id,
            "span_id": result.span_id,
            "status": result.status,
            "blocked": result.blocked,
            "block_code": result.block_code,
            "explanation": result.explanation,
            "outcome": dict(result.outcome),
            "steps": [_serialize(step) for step in result.steps],
            "decision": _serialize(result.decision) if result.decision else None,
            "events": events,
        }
        with self._lock:
            self._records[result.trace_id] = record
            if self._path is not None:
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, sort_keys=True) + "\n")

    def get(self, trace_id: str) -> dict[str, Any] | None:
        key = str(trace_id or "").strip()
        if not key:
            raise ValueError("trace_id is required")
        with self._lock:
            return self._records.get(key)

    def list_trace_ids(self) -> list[str]:
        with self._lock:
            return sorted(self._records.keys())
