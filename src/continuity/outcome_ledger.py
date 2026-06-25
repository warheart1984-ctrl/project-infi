"""Outcome Ledger — constitutional OutcomeObject store (UGR-OUT-1)."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.continuity.outcome_fitness import (
    OutcomeConfig,
    classify_variance,
    compute_variance,
)

OUTCOME_LEDGER_SPEC_ID = "OUTCOME-LEDGER"
OUTCOME_LEDGER_GENESIS_ENTRY_ID = "OUT-LEDGER-0000"
OUTCOME_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "outcome_ledger.sql"


class OutcomeStatus(str, Enum):
    RECORDED = "recorded"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


class OutcomeLedgerEntryType(str, Enum):
    OUTCOME_GENESIS = "OUTCOME_GENESIS"
    OUTCOME_RECORD = "OUTCOME_RECORD"
    OUTCOME_DISPUTE = "OUTCOME_DISPUTE"
    OUTCOME_SUPERSEDE = "OUTCOME_SUPERSEDE"


@dataclass
class OutcomeRecord:
    id: str
    decision_id: str
    expected: dict[str, Any]
    observed: dict[str, Any]
    variance: dict[str, Any]
    lessons: list[str] = field(default_factory=list)
    epoch: int = 0
    status: OutcomeStatus = OutcomeStatus.RECORDED
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "decision_id": self.decision_id,
            "expected": dict(self.expected),
            "observed": dict(self.observed),
            "variance": dict(self.variance),
            "lessons": list(self.lessons),
            "epoch": self.epoch,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> OutcomeRecord:
        return cls(
            id=str(payload["id"]),
            decision_id=str(payload["decision_id"]),
            expected=dict(payload.get("expected") or {}),
            observed=dict(payload.get("observed") or {}),
            variance=dict(payload.get("variance") or {}),
            lessons=[str(item) for item in payload.get("lessons") or []],
            epoch=int(payload.get("epoch") or 0),
            status=OutcomeStatus(str(payload.get("status") or OutcomeStatus.RECORDED.value)),
            timestamp=str(payload.get("timestamp") or ""),
        )


@dataclass(frozen=True, slots=True)
class OutcomeLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: OutcomeLedgerEntryType
    outcome_id: str
    payload: dict[str, Any]
    prev_hash: str | None
    entry_hash: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "epoch": self.epoch,
            "entry_type": self.entry_type.value,
            "outcome_id": self.outcome_id,
            "payload": dict(self.payload),
            "prev_hash": self.prev_hash,
            "hash": self.entry_hash,
            "created_at": self.created_at,
        }


def default_outcome_ledger_path() -> Path:
    override = os.environ.get("OUTCOME_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "outcome-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "outcome-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: OutcomeLedgerEntry) -> str:
    body = entry.to_dict()
    body["hash"] = ""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class OutcomeLedgerStore:
    """SQLite-backed OutcomeObject ledger."""

    def __init__(self, path: Path | None = None, config: OutcomeConfig | None = None) -> None:
        self.path = path or default_outcome_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or OutcomeConfig()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        sql = OUTCOME_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)
            conn.commit()

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT hash FROM outcome_ledger ORDER BY rowid DESC LIMIT 1").fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT COUNT(*) AS c FROM outcome_ledger").fetchone()
        count = int(row["c"]) if row else 0
        return f"OUT-ENTRY-{count + 1:04d}"

    def record(
        self,
        *,
        decision_id: str,
        expected: dict[str, Any],
        observed: dict[str, Any],
        epoch: int,
        outcome_id: str | None = None,
        lessons: list[str] | None = None,
    ) -> OutcomeRecord:
        variance = compute_variance(expected, observed, cfg=self.config)
        classification = classify_variance(variance, cfg=self.config)
        variance_payload = {**variance, "classification": classification}
        record = OutcomeRecord(
            id=outcome_id or f"OUT-{decision_id}-E{epoch}",
            decision_id=decision_id,
            expected=dict(expected),
            observed=dict(observed),
            variance=variance_payload,
            lessons=list(lessons or []),
            epoch=epoch,
            status=OutcomeStatus.RECORDED,
            timestamp=_now_iso(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO outcomes (
                    id, decision_id, expected_json, observed_json,
                    variance_json, lessons_json, epoch, status, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    decision_id = excluded.decision_id,
                    expected_json = excluded.expected_json,
                    observed_json = excluded.observed_json,
                    variance_json = excluded.variance_json,
                    lessons_json = excluded.lessons_json,
                    epoch = excluded.epoch,
                    status = excluded.status,
                    timestamp = excluded.timestamp
                """,
                (
                    record.id,
                    record.decision_id,
                    json.dumps(record.expected, sort_keys=True),
                    json.dumps(record.observed, sort_keys=True),
                    json.dumps(record.variance, sort_keys=True),
                    json.dumps(record.lessons, sort_keys=True),
                    record.epoch,
                    record.status.value,
                    record.timestamp,
                ),
            )
            prev_hash = self._last_entry_hash(conn)
            entry_id = self._next_entry_id(conn)
            draft = OutcomeLedgerEntry(
                entry_id=entry_id,
                epoch=epoch,
                entry_type=OutcomeLedgerEntryType.OUTCOME_RECORD,
                outcome_id=record.id,
                payload={
                    "decision_id": decision_id,
                    "classification": classification,
                    "variance": variance_payload,
                },
                prev_hash=prev_hash,
                entry_hash="",
                created_at=record.timestamp,
            )
            entry_hash = _entry_hash(draft)
            entry = OutcomeLedgerEntry(
                entry_id=draft.entry_id,
                epoch=draft.epoch,
                entry_type=draft.entry_type,
                outcome_id=draft.outcome_id,
                payload=draft.payload,
                prev_hash=draft.prev_hash,
                entry_hash=entry_hash,
                created_at=draft.created_at,
            )
            conn.execute(
                """
                INSERT INTO outcome_ledger (
                    entry_id, epoch, entry_type, outcome_id,
                    payload_json, prev_hash, hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.epoch,
                    entry.entry_type.value,
                    entry.outcome_id,
                    json.dumps(entry.payload, sort_keys=True),
                    entry.prev_hash,
                    entry.entry_hash,
                    entry.created_at,
                ),
            )
            conn.commit()
        return record

    def get(self, outcome_id: str) -> OutcomeRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM outcomes WHERE id = ?", (outcome_id,)).fetchone()
        if row is None:
            return None
        return OutcomeRecord.from_dict(
            {
                "id": row["id"],
                "decision_id": row["decision_id"],
                "expected": json.loads(row["expected_json"] or "{}"),
                "observed": json.loads(row["observed_json"] or "{}"),
                "variance": json.loads(row["variance_json"] or "{}"),
                "lessons": json.loads(row["lessons_json"] or "[]"),
                "epoch": row["epoch"],
                "status": row["status"],
                "timestamp": row["timestamp"],
            }
        )

    def get_by_decision(self, decision_id: str) -> OutcomeRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM outcomes WHERE decision_id = ? ORDER BY timestamp DESC LIMIT 1",
                (decision_id,),
            ).fetchone()
        if row is None:
            return None
        return OutcomeRecord.from_dict(
            {
                "id": row["id"],
                "decision_id": row["decision_id"],
                "expected": json.loads(row["expected_json"] or "{}"),
                "observed": json.loads(row["observed_json"] or "{}"),
                "variance": json.loads(row["variance_json"] or "{}"),
                "lessons": json.loads(row["lessons_json"] or "[]"),
                "epoch": row["epoch"],
                "status": row["status"],
                "timestamp": row["timestamp"],
            }
        )

    def list_outcomes(self, *, epoch: int | None = None) -> list[OutcomeRecord]:
        query = "SELECT * FROM outcomes WHERE 1=1"
        params: list[Any] = []
        if epoch is not None:
            query += " AND epoch = ?"
            params.append(epoch)
        query += " ORDER BY timestamp ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            OutcomeRecord.from_dict(
                {
                    "id": row["id"],
                    "decision_id": row["decision_id"],
                    "expected": json.loads(row["expected_json"] or "{}"),
                    "observed": json.loads(row["observed_json"] or "{}"),
                    "variance": json.loads(row["variance_json"] or "{}"),
                    "lessons": json.loads(row["lessons_json"] or "[]"),
                    "epoch": row["epoch"],
                    "status": row["status"],
                    "timestamp": row["timestamp"],
                }
            )
            for row in rows
        ]

    def ledger_entries(self) -> list[OutcomeLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM outcome_ledger ORDER BY rowid ASC").fetchall()
        return [
            OutcomeLedgerEntry(
                entry_id=str(row["entry_id"]),
                epoch=int(row["epoch"]),
                entry_type=OutcomeLedgerEntryType(str(row["entry_type"])),
                outcome_id=str(row["outcome_id"]),
                payload=json.loads(row["payload_json"] or "{}"),
                prev_hash=row["prev_hash"],
                entry_hash=str(row["hash"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]


def bootstrap_outcome_ledger(store: OutcomeLedgerStore | None = None, *, epoch: int = 17) -> dict[str, Any]:
    ledger = store or OutcomeLedgerStore()
    if ledger.get("OUT-2026-0007") is not None:
        return {"seed_outcome_id": "OUT-2026-0007"}

    expected = {
        "description": "Phase 17 cockpit deployed successfully",
        "metrics": {
            "spine_health_delta": 0.12,
            "cit_improvement": 0.08,
            "operator_latency_ms": -120,
        },
    }
    observed = {
        "description": "Deployment succeeded with minor drift",
        "metrics": {
            "spine_health_delta": 0.10,
            "cit_improvement": 0.07,
            "operator_latency_ms": -125,
        },
    }
    record = ledger.record(
        outcome_id="OUT-2026-0007",
        decision_id="DEC-2026-0001",
        expected=expected,
        observed=observed,
        epoch=epoch,
        lessons=[
            "CITStrip render path needs caching",
            "MeaningStrip hydration cost higher than expected",
        ],
    )
    with ledger._connect() as conn:
        prev_hash = ledger._last_entry_hash(conn)
        entry_id = ledger._next_entry_id(conn)
        now = _now_iso()
        draft = OutcomeLedgerEntry(
            entry_id=entry_id,
            epoch=0,
            entry_type=OutcomeLedgerEntryType.OUTCOME_GENESIS,
            outcome_id=OUTCOME_LEDGER_SPEC_ID,
            payload={"spec_id": OUTCOME_LEDGER_SPEC_ID},
            prev_hash=prev_hash,
            entry_hash="",
            created_at=now,
        )
        entry_hash = _entry_hash(draft)
        conn.execute(
            """
            INSERT INTO outcome_ledger (
                entry_id, epoch, entry_type, outcome_id,
                payload_json, prev_hash, hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.entry_id,
                draft.epoch,
                draft.entry_type.value,
                draft.outcome_id,
                json.dumps(draft.payload, sort_keys=True),
                draft.prev_hash,
                entry_hash,
                now,
            ),
        )
        conn.commit()
    return {"seed_outcome_id": record.id, "classification": record.variance.get("classification")}
