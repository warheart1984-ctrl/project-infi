"""Task event store tests."""

from __future__ import annotations

from pathlib import Path

from operator_kernel.events import TaskEventStore


def test_append_and_read_since(tmp_path: Path) -> None:
    store = TaskEventStore(tmp_path / "tasks")
    task_id = "task-test123"
    store.write_meta(task_id, {"goal": "test", "status": "queued"})
    e1 = store.append(task_id, "task_started", {"goal": "test"})
    e2 = store.append(task_id, "tool_called", {"name": "list_files"})
    events = store.read_since(task_id, 0)
    assert len(events) == 2
    assert events[0].seq == e1.seq
    assert events[1].type == "tool_called"
    partial = store.read_since(task_id, e1.seq)
    assert len(partial) == 1
