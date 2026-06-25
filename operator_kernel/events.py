"""Append-only task event store (JSONL + in-memory fan-out)."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operator_kernel.contracts import AgentEvent


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskEventStore:
    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[threading.Condition]] = {}
        self._seq: dict[str, int] = {}

    def task_dir(self, task_id: str) -> Path:
        path = self.tasks_dir / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def events_path(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "events.jsonl"

    def append(self, task_id: str, event_type: str, payload: dict[str, Any]) -> AgentEvent:
        with self._lock:
            seq = self._seq.get(task_id, 0) + 1
            self._seq[task_id] = seq
            event = AgentEvent(
                type=event_type,
                task_id=task_id,
                seq=seq,
                timestamp=_utc_now(),
                payload=payload,
            )
            line = event.model_dump_json()
            with self.events_path(task_id).open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

            for condition in self._subscribers.get(task_id, []):
                with condition:
                    condition.notify_all()
            return event

    def read_since(self, task_id: str, after_seq: int = 0) -> list[AgentEvent]:
        path = self.events_path(task_id)
        if not path.is_file():
            return []
        events: list[AgentEvent] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                event = AgentEvent.model_validate(json.loads(line))
                if event.seq > after_seq:
                    events.append(event)
        return events

    def subscribe(self, task_id: str) -> threading.Condition:
        condition = threading.Condition()
        with self._lock:
            self._subscribers.setdefault(task_id, []).append(condition)
        return condition

    def list_tasks(self) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        if not self.tasks_dir.is_dir():
            return summaries
        for child in sorted(self.tasks_dir.iterdir(), key=lambda p: p.name, reverse=True):
            if not child.is_dir():
                continue
            meta_path = child / "meta.json"
            meta: dict[str, Any] = {"task_id": child.name}
            if meta_path.is_file():
                try:
                    meta.update(json.loads(meta_path.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError):
                    pass
            events_path = child / "events.jsonl"
            if events_path.is_file():
                meta["event_count"] = sum(1 for _ in events_path.open("r", encoding="utf-8"))
            summaries.append(meta)
        return summaries

    def write_meta(self, task_id: str, meta: dict[str, Any]) -> None:
        path = self.task_dir(task_id) / "meta.json"
        path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def read_meta(self, task_id: str) -> dict[str, Any]:
        path = self.task_dir(task_id) / "meta.json"
        if not path.is_file():
            return {"task_id": task_id}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data.setdefault("task_id", task_id)
            return data
        except (json.JSONDecodeError, OSError):
            return {"task_id": task_id}

    def read_all_events(self, task_id: str) -> list[AgentEvent]:
        return self.read_since(task_id, 0)

    def task_exists(self, task_id: str) -> bool:
        root = self.tasks_dir / task_id
        return (root / "meta.json").is_file() or (root / "events.jsonl").is_file()
