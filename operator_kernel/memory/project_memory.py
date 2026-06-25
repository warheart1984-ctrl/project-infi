"""Project memory via JSONL nodes (LSG-compatible offline store)."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from operator_kernel.memory.paths import memory_paths


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_id(workspace_root: str | None = None) -> str:
    if workspace_root:
        return workspace_root.replace("\\", "/")
    return os.environ.get("AAIS_WORKSPACE_ROOT", "default")


class ProjectMemory:
    def __init__(self, lsg_dir: Path | None = None) -> None:
        paths = memory_paths()
        self.store_dir = lsg_dir or paths.lsg
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.store_dir / "project_events.jsonl"

    def log_event(
        self,
        project_id: str,
        event_type: str,
        label: str,
        data: dict[str, Any] | None = None,
        *,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        node = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "task_id": task_id,
            "type": event_type,
            "label": label,
            "data": data or {},
            "timestamp": _utc_now(),
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(node, ensure_ascii=False) + "\n")
        return node

    def recent_events(self, project_id: str, *, limit: int = 40) -> list[dict[str, Any]]:
        if not self.events_path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        with self.events_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if item.get("project_id") == project_id:
                    rows.append(item)
        return rows[-limit:]

    def summarize_for_prompt(
        self,
        project_id: str,
        files_in_intent: list[str] | None = None,
        *,
        limit: int = 12,
    ) -> str:
        events = self.recent_events(project_id, limit=limit)
        if not events:
            return ""
        decisions: list[str] = []
        failures: list[str] = []
        files: list[str] = []
        for ev in events:
            etype = str(ev.get("type") or "")
            label = str(ev.get("label") or "")
            if etype == "decision" and label:
                decisions.append(label)
            elif etype == "failure" and label:
                failures.append(label)
            elif etype == "file" and label:
                files.append(label)
        if files_in_intent:
            for path in files_in_intent:
                if path and path not in files:
                    files.append(path)
        lines = ["Project context:"]
        if decisions:
            lines.append("- Recent decisions: " + "; ".join(decisions[-5:]))
        if failures:
            lines.append("- Recent failures: " + "; ".join(failures[-5:]))
        if files:
            lines.append("- Files touched: " + ", ".join(files[-8:]))
        if len(lines) == 1:
            return ""
        return "\n".join(lines)
