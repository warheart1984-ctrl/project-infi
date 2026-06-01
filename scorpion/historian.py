"""Long-term OS health drift historian."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
import hashlib
import json
from pathlib import Path
from typing import Any, Literal


ClaimLabel = Literal["asserted", "proven", "rejected"]
INDEX_VERSION = "scorpion.health_drift_index.v1"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json_stable(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def build_drift_index_record(
    *,
    case_id: str,
    drift_count: int,
    claim_label: ClaimLabel,
    scan_hash: str,
    previous: dict[str, Any] | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created_at = created_at_utc or datetime.now(UTC).isoformat()
    prior = str((previous or {}).get("claim_label") or "origin")
    transition = f"{prior}->{claim_label}"
    seed = _hash_text(
        _json_stable(
            {
                "case_id": case_id,
                "drift_count": drift_count,
                "scan_hash": scan_hash,
                "created_at_utc": created_at,
            }
        )
    )
    return {
        "index_version": INDEX_VERSION,
        "index_id": f"driftidx-{seed[:16]}",
        "created_at_utc": created_at,
        "case_id": case_id,
        "drift_count": drift_count,
        "claim_label": claim_label,
        "claim_transition": transition,
        "scan_hash": scan_hash,
        "supersedes_index_id": str((previous or {}).get("index_id") or ""),
    }


def append_drift_record(record: dict[str, Any], index_path: Path) -> None:
    target = index_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(_json_stable(record))
        handle.write("\n")


def read_drift_index(index_path: Path) -> list[dict[str, Any]]:
    target = index_path.expanduser().resolve()
    if not target.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError:
                continue
    return entries


def query_drift_window(
    index_path: Path,
    *,
    window: int = 5,
    claim_status: ClaimLabel = "asserted",
) -> dict[str, Any]:
    del claim_status
    entries = read_drift_index(index_path)
    tail = entries[-window:] if window > 0 else entries
    trend = "stable"
    if len(tail) >= 2:
        counts = [int(e.get("drift_count") or 0) for e in tail]
        if counts[-1] > counts[0]:
            trend = "degrading"
        elif counts[-1] < counts[0]:
            trend = "improving"
    return {
        "mode": "drift-window-query",
        "claim_label": "proven" if tail else "asserted",
        "window": window,
        "entries": tail,
        "trend": trend,
    }
