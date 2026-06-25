"""SQLite-backed panel event store for reflexive, steward, and perception panels."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def default_panel_store_path() -> Path:
    override = os.environ.get("NOVA_PANEL_STORE_PATH", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "nova_panel_store.sqlite3"


class PanelStore:
    """Append-only SQLite store for HUD panel lineage."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_panel_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        sql_path = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "panel_store.sql"
        with self._connect() as conn:
            if sql_path.is_file():
                conn.executescript(sql_path.read_text(encoding="utf-8"))
            else:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS panels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        panel_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        steward_identity TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_panels_type ON panels(panel_type);
                    CREATE INDEX IF NOT EXISTS idx_panels_created ON panels(created_at);
                    CREATE TABLE IF NOT EXISTS reflexive_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kind TEXT NOT NULL,
                        epoch_id TEXT NOT NULL,
                        intent_id TEXT,
                        lineage_event_id TEXT NOT NULL,
                        t5_ref_signal_hash TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS steward_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        kind TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS perception_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        intent_id TEXT NOT NULL,
                        epoch_id TEXT NOT NULL,
                        inputs TEXT NOT NULL,
                        outputs TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        anomaly_score REAL NOT NULL
                    );
                    """
                )

    def append_panel(
        self,
        panel_type: str,
        payload: dict[str, Any],
        *,
        steward_identity: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO panels (panel_type, payload_json, steward_identity)
                VALUES (?, ?, ?)
                """,
                (panel_type, json.dumps(payload, sort_keys=True), steward_identity),
            )

    def list_panels(
        self,
        *,
        panel_type: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if panel_type:
                rows = conn.execute(
                    """
                    SELECT id, panel_type, payload_json, steward_identity, created_at
                    FROM panels WHERE panel_type = ?
                    ORDER BY id ASC LIMIT ?
                    """,
                    (panel_type, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, panel_type, payload_json, steward_identity, created_at
                    FROM panels ORDER BY id ASC LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "id": row["id"],
                "panel_type": row["panel_type"],
                "payload": json.loads(row["payload_json"] or "{}"),
                "steward_identity": row["steward_identity"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def append_reflexive_event(self, event: dict[str, Any]) -> None:
        payload = dict(event.get("payload") or {})
        steward = str(event.get("steward_identity") or payload.get("steward_id") or "")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reflexive_events (
                    kind, epoch_id, intent_id, lineage_event_id,
                    t5_ref_signal_hash, payload, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.get("kind") or ""),
                    str(event.get("epoch_id") or ""),
                    event.get("intent_id"),
                    str(event.get("lineage_event_id") or ""),
                    str(event.get("t5_ref_signal_hash") or ""),
                    json.dumps(payload),
                    str(event.get("timestamp") or ""),
                ),
            )
        self.append_panel("reflexive", event, steward_identity=steward or None)

    def list_reflexive_events(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT kind, epoch_id, intent_id, lineage_event_id, "
                "t5_ref_signal_hash, payload, timestamp FROM reflexive_events ORDER BY id ASC"
            ).fetchall()
        return [
            {
                "kind": row["kind"],
                "epoch_id": row["epoch_id"],
                "intent_id": row["intent_id"],
                "lineage_event_id": row["lineage_event_id"],
                "t5_ref_signal_hash": row["t5_ref_signal_hash"],
                "payload": json.loads(row["payload"] or "{}"),
                "timestamp": row["timestamp"],
            }
            for row in rows
        ]

    def append_steward_event(
        self,
        event: dict[str, Any] | None = None,
        *,
        kind: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        if event is not None:
            record = dict(event)
            kind = str(record.get("kind") or kind or "")
        else:
            record = {"kind": kind, **(payload or {})}
            kind = str(kind or record.get("kind") or "")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO steward_events (kind, payload, created_at) VALUES (?, ?, ?)",
                (
                    kind,
                    json.dumps(record),
                    str(record.get("created_at") or record.get("ratified_at") or ""),
                ),
            )
        steward = str(record.get("steward_id") or record.get("steward_identity") or "")
        self.append_panel("steward", record, steward_identity=steward or None)

    def list_steward_events(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM steward_events ORDER BY id ASC"
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def append_perception_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO perception_snapshots (
                    intent_id, epoch_id, inputs, outputs, confidence, anomaly_score
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(snapshot.get("intent_id") or ""),
                    str(snapshot.get("epoch_id") or ""),
                    json.dumps(snapshot.get("inputs") or {}),
                    json.dumps(snapshot.get("outputs") or {}),
                    float(snapshot.get("confidence") or 0.0),
                    float(snapshot.get("anomaly_score") or 0.0),
                ),
            )
        steward = str((snapshot.get("inputs") or {}).get("steward", {}).get("steward_id") or "")
        self.append_panel("perception", snapshot, steward_identity=steward or None)

    def list_perception_snapshots(self, *, epoch_id: str | None = None) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if epoch_id:
                rows = conn.execute(
                    "SELECT intent_id, epoch_id, inputs, outputs, confidence, anomaly_score "
                    "FROM perception_snapshots WHERE epoch_id = ? ORDER BY id ASC",
                    (epoch_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT intent_id, epoch_id, inputs, outputs, confidence, anomaly_score "
                    "FROM perception_snapshots ORDER BY id ASC"
                ).fetchall()
        return [
            {
                "intent_id": row["intent_id"],
                "epoch_id": row["epoch_id"],
                "inputs": json.loads(row["inputs"] or "{}"),
                "outputs": json.loads(row["outputs"] or "{}"),
                "confidence": float(row["confidence"]),
                "anomaly_score": float(row["anomaly_score"]),
            }
            for row in rows
        ]

    def clear_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM panels")
            conn.execute("DELETE FROM reflexive_events")
            conn.execute("DELETE FROM steward_events")
            conn.execute("DELETE FROM perception_snapshots")

    def clear_reflexive(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM reflexive_events")

    def clear_steward(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM steward_events")

    def clear_perception(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM perception_snapshots")


_STORE: PanelStore | None = None


def get_panel_store() -> PanelStore:
    global _STORE
    if _STORE is None:
        _STORE = PanelStore()
    return _STORE


def reset_panel_store(store: PanelStore | None = None) -> None:
    global _STORE
    _STORE = store
