"""Continuity SQLite store — identity snapshots and governed spine events."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CONTINUITY_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "continuity.sql"


def default_continuity_path() -> Path:
    override = os.environ.get("CONTINUITY_STORE_PATH", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "continuity.sqlite3"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ContinuityStore:
    """Append-only continuity evidence for governed missions."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_continuity_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            if CONTINUITY_SQL.is_file():
                conn.executescript(CONTINUITY_SQL.read_text(encoding="utf-8"))
            else:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS identity_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        steward_identity TEXT NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS continuity_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS assets (
                        id TEXT PRIMARY KEY,
                        asset_type TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        steward_identity TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS invariant_status (
                        invariant_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        last_run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        detail_json TEXT NOT NULL DEFAULT '{}'
                    );
                    """
                )

    def record_identity_snapshot(
        self,
        steward_identity: str,
        snapshot: dict[str, Any],
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO identity_snapshots (steward_identity, snapshot_json, created_at)
                VALUES (?, ?, ?)
                """,
                (steward_identity, json.dumps(snapshot, sort_keys=True), _now()),
            )
            return int(cursor.lastrowid or 0)

    def record_event(self, event_type: str, payload: dict[str, Any]) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO continuity_events (event_type, payload_json, created_at)
                VALUES (?, ?, ?)
                """,
                (event_type, json.dumps(payload, sort_keys=True), _now()),
            )
            return int(cursor.lastrowid or 0)

    def list_events(
        self,
        *,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if event_type:
                rows = conn.execute(
                    """
                    SELECT id, event_type, payload_json, created_at
                    FROM continuity_events
                    WHERE event_type = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (event_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, event_type, payload_json, created_at
                    FROM continuity_events
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def list_identity_snapshots(
        self,
        *,
        steward_identity: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if steward_identity:
                rows = conn.execute(
                    """
                    SELECT id, steward_identity, snapshot_json, created_at
                    FROM identity_snapshots
                    WHERE steward_identity = ?
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (steward_identity, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, steward_identity, snapshot_json, created_at
                    FROM identity_snapshots
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "id": row["id"],
                "steward_identity": row["steward_identity"],
                "snapshot": json.loads(row["snapshot_json"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


_STORE: ContinuityStore | None = None


def get_continuity_store() -> ContinuityStore:
    global _STORE
    if _STORE is None:
        _STORE = ContinuityStore()
    return _STORE


def reset_continuity_store(store: ContinuityStore | None = None) -> None:
    global _STORE
    _STORE = store
