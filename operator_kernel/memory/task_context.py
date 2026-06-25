"""Task memory helpers for planner context."""

from __future__ import annotations

from typing import Any

from operator_kernel.events import TaskEventStore


def build_messages_from_task(
    store: TaskEventStore,
    task_id: str,
    *,
    limit: int = 20,
) -> list[dict[str, str]]:
    meta = store.read_meta(task_id)
    messages = list(meta.get("messages") or [])
    trimmed = messages[-limit:] if limit > 0 else messages
    return [
        {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
        for m in trimmed
        if isinstance(m, dict) and str(m.get("content") or "").strip()
    ]


def task_summary_block(store: TaskEventStore, task_id: str) -> str | None:
    meta = store.read_meta(task_id)
    summary = str(meta.get("summary") or "").strip()
    if summary:
        return f"Task summary:\n{summary}"
    title = str(meta.get("title") or meta.get("goal") or "").strip()
    status = str(meta.get("status") or "").strip()
    if not title:
        return None
    lines = [f"- Goal: {title}"]
    if status:
        lines.append(f"- Status: {status}")
    return "Task summary:\n" + "\n".join(lines)


def update_task_summary(store: TaskEventStore, task_id: str, summary: str) -> dict[str, Any]:
    meta = store.read_meta(task_id)
    meta["summary"] = summary.strip()
    store.write_meta(task_id, meta)
    return meta
