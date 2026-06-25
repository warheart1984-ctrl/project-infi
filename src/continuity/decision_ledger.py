"""Decision Ledger — constitutional DecisionObject lifecycle (UGR-RTC-1)."""

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

DECISION_LEDGER_SPEC_ID = "DECISION-LEDGER"
DECISION_LEDGER_GENESIS_ENTRY_ID = "DEC-LEDGER-0000"
DECISION_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "decision_ledger.sql"

DEFAULT_IDENTITY_ID = "CIV-CORE-01"
DEFAULT_STEWARD_ACTOR = "ROLE-STEWARD-01"


class DecisionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    EXECUTING = "executing"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DecisionLedgerEntryType(str, Enum):
    DECISION_GENESIS = "DECISION_GENESIS"
    DECISION_PROPOSE = "DECISION_PROPOSE"
    DECISION_APPROVE = "DECISION_APPROVE"
    DECISION_REJECT = "DECISION_REJECT"
    DECISION_EXECUTE = "DECISION_EXECUTE"


@dataclass
class DecisionRecord:
    id: str
    actor_id: str
    identity_id: str
    intent: str
    type: str
    evidence_refs: list[str]
    risk_profile: dict[str, Any]
    governance_basis: dict[str, Any]
    resource_plan: dict[str, Any]
    status: DecisionStatus
    epoch: int
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "identity_id": self.identity_id,
            "intent": self.intent,
            "type": self.type,
            "evidence_refs": list(self.evidence_refs),
            "risk_profile": dict(self.risk_profile),
            "governance_basis": dict(self.governance_basis),
            "resource_plan": dict(self.resource_plan),
            "status": self.status.value,
            "epoch": self.epoch,
            "tags": list(self.tags),
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DecisionRecord:
        return cls(
            id=str(payload["id"]),
            actor_id=str(payload["actor_id"]),
            identity_id=str(payload["identity_id"]),
            intent=str(payload["intent"]),
            type=str(payload["type"]),
            evidence_refs=[str(item) for item in payload.get("evidence_refs") or []],
            risk_profile=dict(payload.get("risk_profile") or {}),
            governance_basis=dict(payload.get("governance_basis") or {}),
            resource_plan=dict(payload.get("resource_plan") or {}),
            status=DecisionStatus(str(payload["status"])),
            epoch=int(payload["epoch"]),
            tags=[str(item) for item in payload.get("tags") or []],
            notes=str(payload.get("notes") or ""),
            created_at=str(payload.get("created_at") or ""),
            updated_at=str(payload.get("updated_at") or ""),
        )

    def with_status(self, status: DecisionStatus, *, updated_at: str | None = None) -> DecisionRecord:
        now = updated_at or _now_iso()
        return DecisionRecord(
            id=self.id,
            actor_id=self.actor_id,
            identity_id=self.identity_id,
            intent=self.intent,
            type=self.type,
            evidence_refs=list(self.evidence_refs),
            risk_profile=dict(self.risk_profile),
            governance_basis=dict(self.governance_basis),
            resource_plan=dict(self.resource_plan),
            status=status,
            epoch=self.epoch,
            tags=list(self.tags),
            notes=self.notes,
            created_at=self.created_at,
            updated_at=now,
        )


@dataclass(frozen=True, slots=True)
class DecisionLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: DecisionLedgerEntryType
    decision_id: str
    payload: dict[str, Any]
    prev_hash: str | None
    entry_hash: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "epoch": self.epoch,
            "entry_type": self.entry_type.value,
            "decision_id": self.decision_id,
            "payload": dict(self.payload),
            "prev_hash": self.prev_hash,
            "hash": self.entry_hash,
            "created_at": self.created_at,
        }


def default_decision_ledger_path() -> Path:
    override = os.environ.get("DECISION_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "decision-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "decision-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: DecisionLedgerEntry) -> str:
    body = entry.to_dict()
    body["hash"] = ""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class DecisionLedgerStore:
    """SQLite-backed DecisionObject ledger."""

    def __init__(self, path: Path | str | None = None) -> None:
        if path == ":memory:":
            self.path = Path(":memory:")
        else:
            self.path = Path(path) if path else default_decision_ledger_path()
        if self.path != Path(":memory:"):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @classmethod
    def in_memory(cls) -> DecisionLedgerStore:
        store = object.__new__(cls)
        store.path = Path("file:decision_ledger_mem?mode=memory&cache=shared")
        store._uri = True
        store._init_schema()
        return store

    def _connect(self) -> sqlite3.Connection:
        if getattr(self, "_uri", False):
            conn = sqlite3.connect(str(self.path), uri=True)
        else:
            conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        sql = DECISION_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)
            conn.commit()

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT hash FROM decision_ledger ORDER BY rowid DESC LIMIT 1").fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT COUNT(*) AS c FROM decision_ledger").fetchone()
        count = int(row["c"]) if row else 0
        return f"DEC-ENTRY-{count + 1:04d}"

    def upsert(self, record: DecisionRecord) -> DecisionRecord:
        now = _now_iso()
        if not record.created_at:
            record = DecisionRecord.from_dict(
                {**record.to_dict(), "created_at": now, "updated_at": now}
            )
        elif not record.updated_at:
            record = record.with_status(record.status, updated_at=now)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO decisions (
                    id, actor_id, identity_id, intent, type,
                    evidence_refs_json, risk_profile_json, governance_basis_json,
                    resource_plan_json, status, epoch, tags_json, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    actor_id = excluded.actor_id,
                    identity_id = excluded.identity_id,
                    intent = excluded.intent,
                    type = excluded.type,
                    evidence_refs_json = excluded.evidence_refs_json,
                    risk_profile_json = excluded.risk_profile_json,
                    governance_basis_json = excluded.governance_basis_json,
                    resource_plan_json = excluded.resource_plan_json,
                    status = excluded.status,
                    epoch = excluded.epoch,
                    tags_json = excluded.tags_json,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
                """,
                (
                    record.id,
                    record.actor_id,
                    record.identity_id,
                    record.intent,
                    record.type,
                    json.dumps(record.evidence_refs, sort_keys=True),
                    json.dumps(record.risk_profile, sort_keys=True),
                    json.dumps(record.governance_basis, sort_keys=True),
                    json.dumps(record.resource_plan, sort_keys=True),
                    record.status.value,
                    record.epoch,
                    json.dumps(record.tags, sort_keys=True),
                    record.notes,
                    record.created_at,
                    record.updated_at,
                ),
            )
            conn.commit()
        return record

    def _append_entry(
        self,
        *,
        decision_id: str,
        epoch: int,
        entry_type: DecisionLedgerEntryType,
        payload: dict[str, Any],
    ) -> DecisionLedgerEntry:
        now = _now_iso()
        with self._connect() as conn:
            prev_hash = self._last_entry_hash(conn)
            entry_id = self._next_entry_id(conn)
            draft = DecisionLedgerEntry(
                entry_id=entry_id,
                epoch=epoch,
                entry_type=entry_type,
                decision_id=decision_id,
                payload=payload,
                prev_hash=prev_hash,
                entry_hash="",
                created_at=now,
            )
            entry_hash = _entry_hash(draft)
            entry = DecisionLedgerEntry(
                entry_id=draft.entry_id,
                epoch=draft.epoch,
                entry_type=draft.entry_type,
                decision_id=draft.decision_id,
                payload=draft.payload,
                prev_hash=draft.prev_hash,
                entry_hash=entry_hash,
                created_at=draft.created_at,
            )
            conn.execute(
                """
                INSERT INTO decision_ledger (
                    entry_id, epoch, entry_type, decision_id,
                    payload_json, prev_hash, hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.epoch,
                    entry.entry_type.value,
                    entry.decision_id,
                    json.dumps(entry.payload, sort_keys=True),
                    entry.prev_hash,
                    entry.entry_hash,
                    entry.created_at,
                ),
            )
            conn.commit()
        return entry

    def get(self, decision_id: str) -> DecisionRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
        if row is None:
            return None
        return DecisionRecord.from_dict(
            {
                "id": row["id"],
                "actor_id": row["actor_id"],
                "identity_id": row["identity_id"],
                "intent": row["intent"],
                "type": row["type"],
                "evidence_refs": json.loads(row["evidence_refs_json"] or "[]"),
                "risk_profile": json.loads(row["risk_profile_json"] or "{}"),
                "governance_basis": json.loads(row["governance_basis_json"] or "{}"),
                "resource_plan": json.loads(row["resource_plan_json"] or "{}"),
                "status": row["status"],
                "epoch": row["epoch"],
                "tags": json.loads(row["tags_json"] or "[]"),
                "notes": row["notes"] or "",
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def list_decisions(self, *, epoch: int | None = None, status: DecisionStatus | None = None) -> list[DecisionRecord]:
        query = "SELECT * FROM decisions WHERE 1=1"
        params: list[Any] = []
        if epoch is not None:
            query += " AND epoch = ?"
            params.append(epoch)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY created_at ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            DecisionRecord.from_dict(
                {
                    "id": row["id"],
                    "actor_id": row["actor_id"],
                    "identity_id": row["identity_id"],
                    "intent": row["intent"],
                    "type": row["type"],
                    "evidence_refs": json.loads(row["evidence_refs_json"] or "[]"),
                    "risk_profile": json.loads(row["risk_profile_json"] or "{}"),
                    "governance_basis": json.loads(row["governance_basis_json"] or "{}"),
                    "resource_plan": json.loads(row["resource_plan_json"] or "{}"),
                    "status": row["status"],
                    "epoch": row["epoch"],
                    "tags": json.loads(row["tags_json"] or "[]"),
                    "notes": row["notes"] or "",
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
            )
            for row in rows
        ]

    def ledger_entries(self) -> list[DecisionLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM decision_ledger ORDER BY rowid ASC").fetchall()
        return [
            DecisionLedgerEntry(
                entry_id=str(row["entry_id"]),
                epoch=int(row["epoch"]),
                entry_type=DecisionLedgerEntryType(str(row["entry_type"])),
                decision_id=str(row["decision_id"]),
                payload=json.loads(row["payload_json"] or "{}"),
                prev_hash=row["prev_hash"],
                entry_hash=str(row["hash"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def propose(self, draft: DecisionRecord) -> DecisionRecord:
        record = draft.with_status(DecisionStatus.PROPOSED)
        saved = self.upsert(record)
        self._append_entry(
            decision_id=saved.id,
            epoch=saved.epoch,
            entry_type=DecisionLedgerEntryType.DECISION_PROPOSE,
            payload={"status": saved.status.value, "intent": saved.intent},
        )
        return saved

    def approve(self, decision_id: str) -> DecisionRecord:
        record = self.get(decision_id)
        if record is None:
            raise KeyError(f"Decision not found: {decision_id}")
        updated = record.with_status(DecisionStatus.APPROVED)
        saved = self.upsert(updated)
        self._append_entry(
            decision_id=saved.id,
            epoch=saved.epoch,
            entry_type=DecisionLedgerEntryType.DECISION_APPROVE,
            payload={"status": saved.status.value},
        )
        return saved

    def mark_executed(self, decision_id: str) -> DecisionRecord:
        record = self.get(decision_id)
        if record is None:
            raise KeyError(f"Decision not found: {decision_id}")
        updated = record.with_status(DecisionStatus.EXECUTED)
        saved = self.upsert(updated)
        self._append_entry(
            decision_id=saved.id,
            epoch=saved.epoch,
            entry_type=DecisionLedgerEntryType.DECISION_EXECUTE,
            payload={"status": saved.status.value},
        )
        return saved


def bootstrap_decision_ledger(store: DecisionLedgerStore | None = None, *, epoch: int = 17) -> dict[str, Any]:
    ledger = store or DecisionLedgerStore()
    if ledger.get("DEC-2026-0001") is not None:
        return {"seed_decision_id": "DEC-2026-0001"}

    now = _now_iso()
    seed = DecisionRecord(
        id="DEC-2026-0001",
        actor_id=DEFAULT_STEWARD_ACTOR,
        identity_id=DEFAULT_IDENTITY_ID,
        intent="Upgrade constitutional cockpit to Phase 17",
        type="constitutional-change",
        evidence_refs=[f"EV-PIT-1-E{epoch}"],
        risk_profile={
            "impact": "high",
            "likelihood": "medium",
            "blast_radius": "constitutional-runtime",
            "notes": "Affects epoch gating and operator cockpit.",
        },
        governance_basis={
            "law_refs": ["PIT-1", "EIT-2", "CIT-1"],
            "contract_refs": ["GOV-CONTRACT-CORE"],
            "authority_chain": [DEFAULT_STEWARD_ACTOR, "COUNCIL-01"],
        },
        resource_plan={
            "resource_refs": ["RES-TIME-OPS-01"],
            "estimated_cost": {"time_hours": 40, "budget_usd": 0, "attention_slots": 5},
        },
        status=DecisionStatus.PROPOSED,
        epoch=epoch,
        tags=["constitutional", "phase-17", "cockpit"],
        notes="Phase 17 unified spine cockpit deployment.",
        created_at=now,
        updated_at=now,
    )
    ledger.propose(seed)
    ledger.approve(seed.id)
    ledger.mark_executed(seed.id)
    ledger._append_entry(
        decision_id=DECISION_LEDGER_SPEC_ID,
        epoch=0,
        entry_type=DecisionLedgerEntryType.DECISION_GENESIS,
        payload={"spec_id": DECISION_LEDGER_SPEC_ID},
    )
    return {"seed_decision_id": seed.id}
