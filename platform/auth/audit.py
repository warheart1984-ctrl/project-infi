"""Append-only platform audit stream."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.datetime_compat import UTC

if TYPE_CHECKING:
    from platform.store import PlatformStore


def append_audit_event(
    *,
    audit_path: Path,
    org_id: str,
    principal_id: str,
    action: str,
    job_id: str = "",
    ref_id: str = "",
    details: dict[str, Any] | None = None,
    store: "PlatformStore | None" = None,
) -> dict[str, Any]:
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "org_id": org_id,
        "principal_id": principal_id,
        "action": action,
        "job_id": job_id,
        "ref_id": ref_id,
        "details": details or {},
    }
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    if store and org_id:
        from platform.ledger.hooks import ledger_audit

        ledger_audit(store=store, record=record)
    return record
