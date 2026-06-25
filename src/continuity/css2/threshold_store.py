"""SQLite persistence for RA-COS threshold registry and recalibration ledger."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.continuity.css2.models import RecalibrationEvent
from src.continuity.css2.threshold import Threshold, ThresholdDelta

RA_COS_SQL = Path(__file__).resolve().parents[3] / "fixtures" / "continuity" / "ra_cos_threshold.sql"


def default_racos_store_path() -> Path:
    override = os.environ.get("RACOS_STORE_PATH", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "data" / "ra_cos.sqlite3"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ThresholdVersion:
    threshold_id: str
    version: int
    snapshot: Threshold
    delta_rationale: str
    recalibration_event_id: str | None
    created_at: str
    created_by: str


class RacosThresholdStore:
    """Durable threshold registry, version history, and recalibration event ledger."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_racos_store_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            if RA_COS_SQL.is_file():
                conn.executescript(RA_COS_SQL.read_text(encoding="utf-8"))
            else:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS thresholds (
                        id TEXT PRIMARY KEY,
                        snapshot_json TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS threshold_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        threshold_id TEXT NOT NULL,
                        version INTEGER NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        delta_rationale TEXT NOT NULL DEFAULT '',
                        recalibration_event_id TEXT,
                        created_at TEXT NOT NULL,
                        created_by TEXT NOT NULL,
                        UNIQUE(threshold_id, version)
                    );
                    CREATE TABLE IF NOT EXISTS recalibration_events (
                        event_id TEXT PRIMARY KEY,
                        decision TEXT NOT NULL,
                        threshold_id TEXT,
                        event_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS observation_patterns (
                        id TEXT PRIMARY KEY,
                        pattern_json TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

    def is_empty(self) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM thresholds").fetchone()
        return int(row["n"] if row else 0) == 0

    def seed_from_list(self, thresholds: list[Threshold]) -> None:
        """Idempotent upsert: insert missing thresholds with version 1 history."""
        now = _now_iso()
        with self._connect() as conn:
            for th in thresholds:
                existing = conn.execute(
                    "SELECT id FROM thresholds WHERE id = ?",
                    (th.id,),
                ).fetchone()
                payload = th.model_dump_json()
                if existing:
                    continue
                conn.execute(
                    """
                    INSERT INTO thresholds (id, snapshot_json, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (th.id, payload, th.last_updated_at or now),
                )
                conn.execute(
                    """
                    INSERT INTO threshold_versions (
                        threshold_id, version, snapshot_json, delta_rationale,
                        recalibration_event_id, created_at, created_by
                    )
                    VALUES (?, 1, ?, 'initial', NULL, ?, ?)
                    """,
                    (th.id, payload, th.created_at or now, th.created_by),
                )
            conn.commit()

    def load_thresholds(self) -> list[Threshold]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT snapshot_json FROM thresholds ORDER BY id"
            ).fetchall()
        return [Threshold.model_validate_json(row["snapshot_json"]) for row in rows]

    def get_threshold(self, threshold_id: str) -> Threshold | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT snapshot_json FROM thresholds WHERE id = ?",
                (threshold_id,),
            ).fetchone()
        if row is None:
            return None
        return Threshold.model_validate_json(row["snapshot_json"])

    def get_history(self, threshold_id: str) -> list[ThresholdVersion]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT threshold_id, version, snapshot_json, delta_rationale,
                       recalibration_event_id, created_at, created_by
                FROM threshold_versions
                WHERE threshold_id = ?
                ORDER BY version ASC
                """,
                (threshold_id,),
            ).fetchall()
        return [
            ThresholdVersion(
                threshold_id=row["threshold_id"],
                version=int(row["version"]),
                snapshot=Threshold.model_validate_json(row["snapshot_json"]),
                delta_rationale=row["delta_rationale"] or "",
                recalibration_event_id=row["recalibration_event_id"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            for row in rows
        ]

    def record_recalibration_event(
        self,
        event: RecalibrationEvent,
        *,
        threshold_id: str | None = None,
    ) -> None:
        resolved_id = threshold_id
        if resolved_id is None and event.proposed_changes:
            change = event.proposed_changes[0]
            for th in self.load_thresholds():
                if th.metric == change.metric_id:
                    resolved_id = th.id
                    break

        payload = event.model_dump(mode="json")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO recalibration_events (
                    event_id, decision, threshold_id, event_json, created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.decision,
                    resolved_id,
                    json.dumps(payload, sort_keys=True),
                    event.timestamp.isoformat().replace("+00:00", "Z"),
                ),
            )
            conn.commit()

    def apply_threshold_update(
        self,
        delta: ThresholdDelta,
        *,
        event_id: str,
        actor_id: str,
    ) -> Threshold:
        updated = delta.after.model_copy(
            update={
                "last_updated_at": delta.proposed_at,
                "last_updated_by": actor_id,
            }
        )
        payload = updated.model_dump_json()
        now = updated.last_updated_at or _now_iso()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(MAX(version), 0) AS max_v
                FROM threshold_versions
                WHERE threshold_id = ?
                """,
                (delta.threshold_id,),
            ).fetchone()
            next_version = int(row["max_v"] if row else 0) + 1
            conn.execute(
                """
                INSERT OR REPLACE INTO thresholds (id, snapshot_json, updated_at)
                VALUES (?, ?, ?)
                """,
                (delta.threshold_id, payload, now),
            )
            conn.execute(
                """
                INSERT INTO threshold_versions (
                    threshold_id, version, snapshot_json, delta_rationale,
                    recalibration_event_id, created_at, created_by
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    delta.threshold_id,
                    next_version,
                    payload,
                    delta.rationale,
                    event_id,
                    now,
                    actor_id,
                ),
            )
            conn.commit()
        return updated

    def list_recalibration_events(
        self,
        *,
        decision: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if decision:
                rows = conn.execute(
                    """
                    SELECT event_id, decision, threshold_id, event_json, created_at
                    FROM recalibration_events
                    WHERE decision = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (decision, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT event_id, decision, threshold_id, event_json, created_at
                    FROM recalibration_events
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [
            {
                "event_id": row["event_id"],
                "decision": row["decision"],
                "threshold_id": row["threshold_id"],
                "event": json.loads(row["event_json"] or "{}"),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def count_rows(self) -> dict[str, int]:
        with self._connect() as conn:
            thresholds = conn.execute("SELECT COUNT(*) AS n FROM thresholds").fetchone()
            versions = conn.execute("SELECT COUNT(*) AS n FROM threshold_versions").fetchone()
            events = conn.execute("SELECT COUNT(*) AS n FROM recalibration_events").fetchone()
        return {
            "thresholds": int(thresholds["n"] if thresholds else 0),
            "threshold_versions": int(versions["n"] if versions else 0),
            "recalibration_events": int(events["n"] if events else 0),
        }
