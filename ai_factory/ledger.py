"""Factory ledger — monotonic append-only build history."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_factory.common import DEFAULT_LEDGER_PATH
from src.datetime_compat import UTC


def append_ledger_entry(
    entry: dict[str, Any],
    *,
    ledger_path: Path | None = None,
) -> dict[str, Any]:
    target = (ledger_path or DEFAULT_LEDGER_PATH).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    record = dict(entry)
    record.setdefault("recorded_at_utc", datetime.now(UTC).isoformat())
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def read_ledger(*, ledger_path: Path | None = None) -> list[dict[str, Any]]:
    target = (ledger_path or DEFAULT_LEDGER_PATH).expanduser().resolve()
    if not target.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def find_ledger_entry(
    build_id: str,
    *,
    ledger_path: Path | None = None,
) -> dict[str, Any] | None:
    matches = [item for item in read_ledger(ledger_path=ledger_path) if item.get("build_id") == build_id]
    return matches[-1] if matches else None
