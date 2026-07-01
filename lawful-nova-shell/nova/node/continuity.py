from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from nova.node.ledger import append_jsonl, read_jsonl, runtime_dir, stable_hash


def continuity_log_path():
    return runtime_dir() / "continuity.jsonl"


def append_event(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "event_id": f"{kind}-{uuid4()}",
        "timestamp": int(time.time()),
        "kind": kind,
        "data": data,
    }
    return append_jsonl(continuity_log_path(), entry)


def append_receipt(entry: dict[str, Any]) -> dict[str, Any]:
    return append_jsonl(continuity_log_path(), entry)


def read_events() -> list[dict[str, Any]]:
    return read_jsonl(continuity_log_path())


def last_receipt_hash() -> str | None:
    events = read_events()
    if not events:
        return None
    last = events[-1]
    return str(last.get("receipt_hash") or stable_hash(last))
