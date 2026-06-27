"""Append-only governance event ledger for lawful Nova turns."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def ledger_path() -> Path | None:
    raw = os.environ.get("NOVA_GOVERNANCE_LEDGER_PATH", "").strip()
    if not raw:
        return None
    return Path(raw)


def append_jsonl(record: dict[str, Any]) -> Path | None:
    path = ledger_path()
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
    return path
