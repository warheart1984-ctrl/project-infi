#!/usr/bin/env python3
"""Create Appwrite governance database + tables (idempotent).

Uses the Python SDK — no Appwrite CLI required. Requires a server API key with
Tables write scope.

Usage (from project-infi root, after copying deploy/appwrite/.env.example):

    pip install appwrite
    set APPWRITE_ENDPOINT=https://<REGION>.cloud.appwrite.io/v1
    set APPWRITE_PROJECT_ID=...
    set APPWRITE_API_KEY=...
    python scripts/appwrite_bootstrap_tables.py

Then enable the sink and index contracts:

    set AAIS_APPWRITE_SINK=1
    set APPWRITE_DATABASE_ID=governance
    python scripts/appwrite_governance_index_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "governance").strip()
GOVERNANCE_TABLE = os.getenv("APPWRITE_GOVERNANCE_TABLE_ID", "governance_contracts").strip()
LEDGER_TABLE = os.getenv("APPWRITE_LEDGER_TABLE_ID", "ledger_events").strip()

GOVERNANCE_COLUMNS = [
    {"key": "path", "type": "varchar", "size": 512, "required": True},
    {"key": "title", "type": "varchar", "size": 255, "required": False},
    {"key": "content", "type": "mediumtext", "required": False},
    {"key": "doc_type", "type": "varchar", "size": 64, "required": False},
    {"key": "indexed_at", "type": "varchar", "size": 32, "required": False},
]

LEDGER_COLUMNS = [
    {"key": "scope_id", "type": "varchar", "size": 128, "required": False},
    {"key": "decision_id", "type": "varchar", "size": 64, "required": False},
    {"key": "decision_kind", "type": "varchar", "size": 64, "required": False},
    {"key": "decision", "type": "varchar", "size": 32, "required": False},
    {"key": "summary", "type": "varchar", "size": 2000, "required": False},
    {"key": "row_hash", "type": "varchar", "size": 128, "required": False},
    {"key": "recorded_at", "type": "varchar", "size": 32, "required": False},
    {"key": "event_json", "type": "mediumtext", "required": False},
]


def _require_env() -> None:
    missing = [
        key
        for key in ("APPWRITE_ENDPOINT", "APPWRITE_PROJECT_ID", "APPWRITE_API_KEY")
        if not os.getenv(key, "").strip()
    ]
    if missing:
        print("Missing required environment variables:", ", ".join(missing))
        print("See deploy/appwrite/.env.example")
        sys.exit(1)


def _client():
    from appwrite.client import Client
    from appwrite.services.tablesdb import TablesDB

    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_ENDPOINT"].rstrip("/"))
        .set_project(os.environ["APPWRITE_PROJECT_ID"])
        .set_key(os.environ["APPWRITE_API_KEY"])
    )
    return TablesDB(client)


def _is_not_found(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code == 404:
        return True
    message = str(exc).lower()
    return "not found" in message or "404" in message


def ensure_database(tables_db) -> None:
    try:
        tables_db.get(DATABASE_ID)
        print(f"Database '{DATABASE_ID}' already exists.")
    except Exception as exc:
        if not _is_not_found(exc):
            raise
        tables_db.create(DATABASE_ID, "Governance")
        print(f"Created database '{DATABASE_ID}'.")


def ensure_table(tables_db, *, table_id: str, name: str, columns: list[dict]) -> None:
    try:
        tables_db.get_table(DATABASE_ID, table_id)
        print(f"Table '{table_id}' already exists.")
        return
    except Exception as exc:
        if not _is_not_found(exc):
            raise
    tables_db.create_table(
        database_id=DATABASE_ID,
        table_id=table_id,
        name=name,
        columns=columns,
    )
    print(f"Created table '{table_id}'.")


def main() -> int:
    _require_env()
    try:
        from appwrite.exception import AppwriteException  # noqa: F401
    except ImportError:
        print("Install the SDK: pip install appwrite")
        return 1

    tables_db = _client()
    ensure_database(tables_db)
    ensure_table(
        tables_db,
        table_id=GOVERNANCE_TABLE,
        name="Governance contracts",
        columns=GOVERNANCE_COLUMNS,
    )
    ensure_table(
        tables_db,
        table_id=LEDGER_TABLE,
        name="Ledger events",
        columns=LEDGER_COLUMNS,
    )
    print()
    print("Bootstrap complete. Next:")
    print("  1. Set AAIS_APPWRITE_SINK=1 and APPWRITE_DATABASE_ID=governance")
    print("  2. python scripts/appwrite_governance_index_demo.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
