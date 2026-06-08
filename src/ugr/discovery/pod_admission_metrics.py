"""In-process counters for Discovery Pod admission outcomes (ops visibility)."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_COUNTERS: dict[str, int] = {}
_LOCK = threading.Lock()


def _increment(key: str, amount: int = 1) -> None:
    with _LOCK:
        _COUNTERS[key] = int(_COUNTERS.get(key) or 0) + amount


def record_admission_admit(reason: str) -> None:
    _increment("admit_total")
    _increment(f"admit:{reason or 'unknown'}")


def record_admission_skip(reason: str) -> None:
    _increment("skip_total")
    _increment(f"skip:{reason or 'unknown'}")


def snapshot_counters() -> dict[str, Any]:
    with _LOCK:
        by_reason = {k: v for k, v in sorted(_COUNTERS.items()) if k.startswith(("skip:", "admit:"))}
        return {
            "admit_total": int(_COUNTERS.get("admit_total") or 0),
            "skip_total": int(_COUNTERS.get("skip_total") or 0),
            "by_reason": by_reason,
        }


def reset_counters() -> None:
    with _LOCK:
        _COUNTERS.clear()


def write_metrics_snapshot(path: str | Path) -> dict[str, Any]:
    """Optional JSON snapshot for external scrapers."""
    payload = snapshot_counters()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
