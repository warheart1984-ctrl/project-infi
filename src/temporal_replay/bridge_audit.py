"""Persist capability bridge audit events for temporal replay."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.temporal_replay.paths import bridge_audit_path, default_runtime_dir


def bridge_audit_enabled() -> bool:
    raw = os.getenv("AAIS_BRIDGE_AUDIT_PERSIST", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def append_bridge_audit_event(
    session_id: str,
    event: dict[str, Any],
    *,
    runtime_dir: Path | None = None,
) -> None:
    if not bridge_audit_enabled():
        return
    sid = str(session_id or "").strip()
    if not sid:
        return
    path = bridge_audit_path(sid, runtime_dir=runtime_dir or default_runtime_dir())
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(event)
    row.setdefault("timestamp", datetime.now(timezone.utc).replace(microsecond=0).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
