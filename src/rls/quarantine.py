"""RLS quarantine event logging."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_QUARANTINE_FILENAME = "rls_quarantine.jsonl"


def _default_quarantine_path() -> Path:
    try:
        from src.temporal_replay.paths import default_runtime_dir

        base = default_runtime_dir()
    except Exception:
        base = Path(
            os.environ.get("AAIS_RUNTIME_DIR")
            or os.environ.get("PROJECT_INFI_RUNTIME", ".runtime")
        )
    return Path(base) / _QUARANTINE_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_quarantine_event(
    *,
    quarantine_id: str,
    graph_id: str,
    violations: list[dict[str, Any]],
    mode: str,
    otem_level: int,
    path: Path | None = None,
) -> dict[str, Any]:
    target = path or _default_quarantine_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "event_type": "rls_quarantine",
        "quarantine_id": quarantine_id,
        "graph_id": graph_id,
        "violations": violations,
        "mode": mode,
        "otem_level": otem_level,
        "recorded_at": _utc_now_iso(),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def recent_quarantine_count(*, limit: int = 100, path: Path | None = None) -> int:
    target = path or _default_quarantine_path()
    if not target.exists():
        return 0
    count = 0
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return min(count, limit) if limit else count


def recent_quarantine_events(*, limit: int = 10, path: Path | None = None) -> list[dict[str, Any]]:
    target = path or _default_quarantine_path()
    if not target.exists():
        return []
    lines: list[str] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                lines.append(line.strip())
    events: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
