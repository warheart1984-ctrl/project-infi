"""Test helpers for federated epoch window fixtures."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def open_amendable_epoch_window(
    reg_path: Path,
    *,
    epoch_id: str | None = None,
    span_days: int = 14,
) -> str:
    """Widen an epoch window so ``datetime.now(UTC)`` is amendable (tests only)."""
    doc = json.loads(reg_path.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=1)).replace(microsecond=0)
    end = (now + timedelta(days=span_days)).replace(microsecond=0)
    target = epoch_id or str(doc.get("default_epoch_id") or "epoch_pilot_002")
    epochs = list(doc.get("epochs") or [])
    matched = False
    for epoch in epochs:
        if str(epoch.get("epoch_id")) == target:
            epoch["epoch_start_utc"] = start.isoformat().replace("+00:00", "Z")
            epoch["epoch_end_utc"] = end.isoformat().replace("+00:00", "Z")
            epoch["frozen"] = False
            epoch["amendable"] = True
            matched = True
            break
    if not matched:
        epochs.append(
            {
                "epoch_id": target,
                "epoch_start_utc": start.isoformat().replace("+00:00", "Z"),
                "epoch_end_utc": end.isoformat().replace("+00:00", "Z"),
                "frozen": False,
                "amendable": True,
            }
        )
    doc["epochs"] = epochs
    doc["default_epoch_id"] = target
    reg_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return target
