"""Hash-chained platform operational ledger."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from src.datetime_compat import UTC

from platform.common import new_id
from platform.store import PlatformStore

ENTRY_VERSION = "platform.platform_ledger_entry.v1"
GENESIS_HASH = "0" * 64


def _compute_hash(*, prev_hash: str, payload: dict[str, Any]) -> str:
    body = json.dumps({"prev_hash": prev_hash, "payload": payload}, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()


def append_ledger_entry(
    *,
    store: PlatformStore,
    org_id: str,
    kind: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    prev = store.get_ledger_tail_hash(org_id=org_id) or GENESIS_HASH
    entry_id = new_id("led")
    body = dict(payload)
    entry_hash = _compute_hash(prev_hash=prev, payload=body)
    record = {
        "entry_version": ENTRY_VERSION,
        "entry_id": entry_id,
        "org_id": org_id,
        "kind": kind,
        "prev_hash": prev,
        "entry_hash": entry_hash,
        "payload": body,
        "created_at": datetime.now(UTC).isoformat(),
    }
    store.append_ledger_entry(record)
    return record


def verify_ledger_chain(*, store: PlatformStore, org_id: str) -> tuple[bool, str]:
    entries = store.list_ledger_entries(org_id=org_id)
    if not entries:
        return True, "empty chain"
    prev = GENESIS_HASH
    for entry in entries:
        if entry.get("prev_hash") != prev:
            return False, f"broken link at {entry.get('entry_id')}"
        expected = _compute_hash(prev_hash=prev, payload=entry.get("payload") or {})
        if entry.get("entry_hash") != expected:
            return False, f"hash mismatch at {entry.get('entry_id')}"
        prev = str(entry.get("entry_hash"))
    return True, "ok"


def query_ledger(
    *,
    store: PlatformStore,
    org_id: str,
    kind: str = "",
    day_from: str = "",
    day_to: str = "",
    cursor: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    entries = store.list_ledger_entries(org_id=org_id, kind=kind, limit=500)
    if cursor:
        found = False
        filtered: list[dict[str, Any]] = []
        for e in entries:
            if found:
                filtered.append(e)
            elif str(e.get("entry_id")) == cursor:
                found = True
        entries = filtered
    if day_from or day_to:
        entries = [
            e
            for e in entries
            if (not day_from or str(e.get("created_at", ""))[:10] >= day_from[:10])
            and (not day_to or str(e.get("created_at", ""))[:10] <= day_to[:10])
        ]
    return {"entries": entries[:limit], "cursor": cursor, "verified_hint": "call /ledger/verify"}


def export_ledger_jsonl(*, store: PlatformStore, org_id: str) -> str:
    lines = []
    for entry in store.list_ledger_entries(org_id=org_id, limit=10000):
        lines.append(json.dumps(entry, sort_keys=True))
    return "\n".join(lines) + ("\n" if lines else "")
