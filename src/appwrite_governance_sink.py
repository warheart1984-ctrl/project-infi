"""Optional Appwrite projection for governance contracts and ledger events.

Mirrors local constitutional truth (JSONL operator ledger, contract files) into
Appwrite Tables for operator dashboards, mobile clients, and cross-device audit
visibility. Disabled unless explicitly configured.

Admission: optional sink only — never the write authority for operator decisions.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

GOVERNANCE_CONTRACTS_TABLE = "governance_contracts"
LEDGER_EVENTS_TABLE = "ledger_events"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def appwrite_sink_enabled() -> bool:
    raw = os.getenv("AAIS_APPWRITE_SINK", "").strip().lower()
    if raw not in {"1", "true", "yes", "on"}:
        return False
    required = (
        "APPWRITE_ENDPOINT",
        "APPWRITE_PROJECT_ID",
        "APPWRITE_API_KEY",
        "APPWRITE_DATABASE_ID",
    )
    return all(os.getenv(key, "").strip() for key in required)


def _client():
    from appwrite.client import Client
    from appwrite.services.tablesdb import TablesDB

    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_ENDPOINT"].rstrip("/"))
        .set_project(os.environ["APPWRITE_PROJECT_ID"])
        .set_key(os.environ["APPWRITE_API_KEY"])
    )
    return client, TablesDB(client)


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def contract_rows_from_paths(paths: list[str], *, root: str | None = None) -> list[dict[str, Any]]:
    from pathlib import Path

    base = Path(root) if root else Path(__file__).resolve().parents[1]
    rows: list[dict[str, Any]] = []
    for rel in paths:
        path = Path(rel)
        if not path.is_absolute():
            path = base / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        rel_posix = str(path.relative_to(base)).replace("\\", "/")
        rows.append(
            {
                "path": rel_posix,
                "title": path.name.replace(".md", "").replace("_", " "),
                "content": text[:12000],
                "doc_type": "contract",
                "indexed_at": _utc_now_iso(),
            }
        )
    return rows


def upsert_governance_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Index governance contract rows into Appwrite Tables (create-only upsert by path)."""
    if not appwrite_sink_enabled():
        return {"enabled": False, "upserted": 0, "skipped": len(rows)}
    if not rows:
        return {"enabled": True, "upserted": 0, "skipped": 0}

    from appwrite.id import ID
    from appwrite.query import Query

    _, tables_db = _client()
    database_id = os.environ["APPWRITE_DATABASE_ID"]
    table_id = os.getenv("APPWRITE_GOVERNANCE_TABLE_ID", GOVERNANCE_CONTRACTS_TABLE).strip()
    upserted = 0

    for row in rows:
        path = str(row.get("path") or "").strip()
        if not path:
            continue
        existing = tables_db.list_rows(
            database_id,
            table_id,
            [Query.equal("path", path), Query.limit(1)],
        )
        documents = existing.get("rows") or existing.get("documents") or []
        payload = {
            "path": path,
            "title": str(row.get("title") or path),
            "content": str(row.get("content") or "")[:12000],
            "doc_type": str(row.get("doc_type") or "contract"),
            "indexed_at": str(row.get("indexed_at") or _utc_now_iso()),
        }
        if documents:
            doc_id = str(documents[0].get("$id") or "")
            tables_db.update_row(database_id, table_id, doc_id, payload)
        else:
            tables_db.create_row(database_id, table_id, ID.unique(), payload)
        upserted += 1

    return {"enabled": True, "upserted": upserted, "skipped": 0}


def mirror_ledger_event(scope_id: str, event: dict[str, Any]) -> dict[str, Any] | None:
    """Best-effort mirror of one operator ledger row into Appwrite."""
    if not appwrite_sink_enabled():
        return None

    from appwrite.id import ID

    _, tables_db = _client()
    database_id = os.environ["APPWRITE_DATABASE_ID"]
    table_id = os.getenv("APPWRITE_LEDGER_TABLE_ID", LEDGER_EVENTS_TABLE).strip()
    payload = {
        "scope_id": str(scope_id or "global"),
        "decision_id": str(event.get("decision_id") or ""),
        "decision_kind": str(event.get("decision_kind") or ""),
        "decision": str(event.get("decision") or ""),
        "summary": str(event.get("summary") or "")[:2000],
        "row_hash": str(event.get("row_hash") or ""),
        "recorded_at": str(event.get("recorded_at") or _utc_now_iso()),
        "event_json": _stable_json(event)[:16000],
    }
    created = tables_db.create_row(database_id, table_id, ID.unique(), payload)
    return created if isinstance(created, dict) else {"id": created}


def maybe_mirror_ledger_event(scope_id: str, event: dict[str, Any]) -> None:
    """Fire-and-forget hook for OperatorDecisionLedgerStore.append."""
    try:
        mirror_ledger_event(scope_id, event)
    except Exception:
        return
