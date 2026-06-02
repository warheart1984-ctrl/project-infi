"""JSONL audit helpers for Alt-4 runtime organs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.governance_organs._paths import runtime_governance_dir


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_audit(name: str, record: dict[str, Any]) -> Path:
    path = runtime_governance_dir() / name
    payload = {"timestamp": _utc_now_iso(), **record}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path
