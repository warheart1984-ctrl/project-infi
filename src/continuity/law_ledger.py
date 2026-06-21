"""Law Ledger — sovereign substrate law lifecycle (LAW-LEDGER-0000, PIT selection kernel)."""

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

from src.continuity.continuity_lattice import lci_holds
from src.continuity.convergence_algebra import (
    DEFAULT_CONVERGENCE_EPSILON,
    DEFAULT_PHI_MIN,
    convergence_fitness,
)
from src.continuity.invariant_engine import DEFAULT_INVARIANT_ENGINE
from src.continuity.lineage import Lineage, continuity_trace, generativity
from src.continuity.lci_stack import LCI_FIXTURE, lineages_from_fixture, load_lci_fixture


LAW_LEDGER_SPEC_ID = "LAW-LEDGER"
LAW_LEDGER_GENESIS_ENTRY_ID = "LAW-LEDGER-0000"
LAW_LEDGER_SPEC_HASH = "hash_law_ledger_spec_v1"
LAW_LEDGER_0001_ID = "LAW-LEDGER-0001"
FOUNDING_LAWS_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "founding_laws.v1.json"
LAW_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "law_ledger.sql"

W_CONT = 0.25
W_CONV = 0.25
W_INV = 0.25
W_SAFE = 0.25

DEFAULT_ADMIT_THRESHOLD = 0.90
DEFAULT_REJECT_THRESHOLD = 0.70


LAW_LEDGER_0001_CANONICAL_TEXT = """LAW LEDGER
Codename: LAW-LEDGER-0001
Purpose: First-class, ledger-tracked sovereign laws with fitness lifecycle.

I. LawRecord — canonical schema for law_records (JSON + SQLite).
II. law_ledger — ROOT-class append-only chain anchored by LAW-LEDGER-0000.
III. LAW_EVAL / LAW_STATUS_CHANGE — payloads reconstruct fitness and lifecycle.
IV. Sovereign Selection Kernel — evaluate_law(G, epoch, lineages) writes ledger entries.
V. Founding Laws — SIT-1 (admitted), GIT-1 (admitted), PIT-1 (experimental quarantine band).
"""


class LawStatus(str, Enum):
    PROPOSED = "proposed"
    EXPERIMENTAL = "experimental"
    ADMITTED = "admitted"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class LawLedgerEntryType(str, Enum):
    LAW_GENESIS = "LAW_GENESIS"
    LAW_EVAL = "LAW_EVAL"
    LAW_STATUS_CHANGE = "LAW_STATUS_CHANGE"


@dataclass
class FitnessHistoryRow:
    epoch: int
    f: float
    sample_size: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch": self.epoch,
            "F": round(self.f, 6),
            "sample_size": self.sample_size,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> FitnessHistoryRow:
        return cls(
            epoch=int(row["epoch"]),
            f=float(row["F"]),
            sample_size=int(row["sample_size"]),
            notes=str(row.get("notes") or ""),
        )


@dataclass
class LawRecord:
    law_id: str
    version: str
    law_hash: str
    spec_ref: str
    status: LawStatus
    created_at_epoch: int
    introduced_by: str
    current_fitness: float
    fitness_history: list[FitnessHistoryRow] = field(default_factory=list)
    admit_threshold: float = DEFAULT_ADMIT_THRESHOLD
    reject_threshold: float = DEFAULT_REJECT_THRESHOLD
    domains: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "law_id": self.law_id,
            "version": self.version,
            "law_hash": self.law_hash,
            "spec_ref": self.spec_ref,
            "status": self.status.value,
            "created_at_epoch": self.created_at_epoch,
            "introduced_by": self.introduced_by,
            "fitness": {
                "current": round(self.current_fitness, 6),
                "history": [row.to_dict() for row in self.fitness_history],
                "thresholds": {
                    "admit": self.admit_threshold,
                    "reject": self.reject_threshold,
                },
            },
            "domains": list(self.domains),
            "dependencies": list(self.dependencies),
            "conflicts": list(self.conflicts),
            "supersedes": list(self.supersedes),
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> LawRecord:
        fitness = row.get("fitness") or {}
        thresholds = fitness.get("thresholds") or {}
        history_rows = [
            FitnessHistoryRow.from_dict(item) for item in fitness.get("history") or []
        ]
        return cls(
            law_id=str(row["law_id"]),
            version=str(row["version"]),
            law_hash=str(row["law_hash"]),
            spec_ref=str(row["spec_ref"]),
            status=LawStatus(str(row["status"])),
            created_at_epoch=int(row["created_at_epoch"]),
            introduced_by=str(row["introduced_by"]),
            current_fitness=float(fitness.get("current") or 0.0),
            fitness_history=history_rows,
            admit_threshold=float(thresholds.get("admit") or DEFAULT_ADMIT_THRESHOLD),
            reject_threshold=float(thresholds.get("reject") or DEFAULT_REJECT_THRESHOLD),
            domains=[str(item) for item in row.get("domains") or []],
            dependencies=[str(item) for item in row.get("dependencies") or []],
            conflicts=[str(item) for item in row.get("conflicts") or []],
            supersedes=[str(item) for item in row.get("supersedes") or []],
        )


@dataclass(frozen=True, slots=True)
class LawLedgerEntry:
    entry_id: str
    prev_hash: str | None
    timestamp: str
    epoch: int
    entry_type: LawLedgerEntryType
    law_id: str
    law_hash: str
    payload: dict[str, Any]
    signed_by: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "epoch": self.epoch,
            "entry_type": self.entry_type.value,
            "law_id": self.law_id,
            "law_hash": self.law_hash,
            "payload": dict(self.payload),
            "signed_by": self.signed_by,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> LawLedgerEntry:
        return cls(
            entry_id=str(row["entry_id"]),
            prev_hash=row.get("prev_hash"),
            timestamp=str(row["timestamp"]),
            epoch=int(row["epoch"]),
            entry_type=LawLedgerEntryType(str(row["entry_type"])),
            law_id=str(row["law_id"]),
            law_hash=str(row["law_hash"]),
            payload=dict(row.get("payload") or {}),
            signed_by=str(row["signed_by"]),
            signature=str(row["signature"]),
        )


def default_law_ledger_path() -> Path:
    override = os.environ.get("LAW_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "law-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "law-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sig(signer: str, entry_id: str) -> str:
    return f"sig({signer}, {entry_id})"


def _entry_hash(entry: LawLedgerEntry) -> str:
    canonical = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def genesis_block() -> LawLedgerEntry:
    return LawLedgerEntry(
        entry_id=LAW_LEDGER_GENESIS_ENTRY_ID,
        prev_hash=None,
        timestamp="EPOCH:0:T0",
        epoch=0,
        entry_type=LawLedgerEntryType.LAW_GENESIS,
        law_id=LAW_LEDGER_SPEC_ID,
        law_hash=LAW_LEDGER_SPEC_HASH,
        payload={
            "description": "Genesis of Law Ledger and LawRecord schema",
            "spec_ref": "ROOT/LAW-LEDGER.md#v1.0.0",
            "initialized_laws": ["SIT-1"],
            "created_by": "ROOT",
        },
        signed_by="ROOT",
        signature=_sig("ROOT", LAW_LEDGER_GENESIS_ENTRY_ID),
    )


def law_eval_payload(
    *,
    law_id: str,
    law_hash: str,
    epoch: int,
    f: float,
    components: dict[str, float],
    sample_size: int,
    thresholds: dict[str, float],
    notes: str,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "type": "LAW_EVAL",
        "law_id": law_id,
        "law_hash": law_hash,
        "epoch": epoch,
        "fitness": {
            "F": round(f, 6),
            "components": {key: round(value, 6) for key, value in components.items()},
            "sample_size": sample_size,
        },
        "thresholds": thresholds,
        "notes": notes,
    }
    if evidence_id:
        payload["evidence_id"] = evidence_id
    return payload


def law_status_change_payload(
    *,
    law_id: str,
    law_hash: str,
    epoch: int,
    old_status: LawStatus,
    new_status: LawStatus,
    reason: str,
    source: str,
    ref_entry_id: str | None,
    evidence_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "type": "LAW_STATUS_CHANGE",
        "law_id": law_id,
        "law_hash": law_hash,
        "epoch": epoch,
        "old_status": old_status.value,
        "new_status": new_status.value,
        "reason": reason,
        "trigger": {
            "source": source,
            "ref_entry_id": ref_entry_id,
        },
    }
    if evidence_id:
        payload["evidence_id"] = evidence_id
    return payload


def continuity_score(lineages: list[Lineage]) -> float:
    if not lineages:
        return 1.0
    traces = [continuity_trace(item) for item in lineages]
    union_size = len(set().union(*traces))
    if union_size == 0:
        return 1.0
    covered = sum(len(trace) for trace in traces) / (len(traces) * union_size)
    return min(1.0, max(0.0, covered))


def convergence_score(
    lineages: list[Lineage],
    *,
    epsilon: float = DEFAULT_CONVERGENCE_EPSILON,
    phi_min: float = DEFAULT_PHI_MIN,
) -> float:
    result = convergence_fitness(lineages, epsilon=epsilon, phi_min=phi_min)
    return float(result["phi"])


def invariant_score(lineages: list[Lineage]) -> float:
    if not lineages:
        return 1.0
    baseline = lineages[0]
    checks = 0
    passed = 0
    for candidate in lineages[1:]:
        checks += 1
        if lci_holds(baseline, candidate):
            passed += 1
        inv = DEFAULT_INVARIANT_ENGINE.validate_lineage_transition(baseline, candidate)
        if inv["passed"]:
            passed += 1
        checks += 1
    if checks == 0:
        inv_only = DEFAULT_INVARIANT_ENGINE.validate_lineage_transition(baseline, baseline)
        return 1.0 if inv_only["passed"] else 0.0
    return passed / checks


def safety_score(lineages: list[Lineage]) -> float:
    if not lineages:
        return 1.0
    min_g = min(generativity(item) for item in lineages)
    max_g = max(generativity(item) for item in lineages)
    if max_g <= 0:
        return 1.0
    ratio = min_g / max_g if max_g else 1.0
    return min(1.0, max(0.0, ratio))


def compute_fitness_components(lineages: list[Lineage]) -> dict[str, float]:
    return {
        "C_cont": continuity_score(lineages),
        "C_conv": convergence_score(lineages),
        "C_inv": invariant_score(lineages),
        "C_safe": safety_score(lineages),
    }


def aggregate_fitness(components: dict[str, float]) -> float:
    return (
        W_CONT * components["C_cont"]
        + W_CONV * components["C_conv"]
        + W_INV * components["C_inv"]
        + W_SAFE * components["C_safe"]
    )


def decide_status(
    old_status: LawStatus,
    f: float,
    *,
    admit: float,
    reject: float,
) -> LawStatus:
    if f >= admit:
        return LawStatus.ADMITTED
    if f < reject:
        return LawStatus.REVOKED if old_status == LawStatus.ADMITTED else LawStatus.REVOKED
    if old_status in {LawStatus.PROPOSED, LawStatus.EXPERIMENTAL}:
        return LawStatus.EXPERIMENTAL
    return LawStatus.QUARANTINED


class LawLedgerStore:
    """SQLite-backed Law Ledger with append-only ROOT-class chain."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_law_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = LAW_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute(
            "SELECT entry_id, prev_hash, timestamp, epoch, entry_type, law_id, law_hash, payload, signed_by, signature "
            "FROM law_ledger ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        entry = LawLedgerEntry.from_dict(
            {
                "entry_id": row["entry_id"],
                "prev_hash": row["prev_hash"],
                "timestamp": row["timestamp"],
                "epoch": row["epoch"],
                "entry_type": row["entry_type"],
                "law_id": row["law_id"],
                "law_hash": row["law_hash"],
                "payload": json.loads(row["payload"] or "{}"),
                "signed_by": row["signed_by"],
                "signature": row["signature"],
            }
        )
        return _entry_hash(entry)

    def _next_entry_id(self, conn: sqlite3.Connection, prefix: str) -> str:
        row = conn.execute(
            "SELECT entry_id FROM law_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            (f"{prefix}-%",),
        ).fetchone()
        if row is None:
            return f"{prefix}-0001"
        tail = str(row["entry_id"]).split("-")[-1]
        next_num = int(tail) + 1
        return f"{prefix}-{next_num:04d}"

    def append_law_ledger_entry(
        self,
        *,
        entry_type: LawLedgerEntryType,
        law_id: str,
        law_hash: str,
        epoch: int,
        payload: dict[str, Any],
        signed_by: str,
        entry_id: str | None = None,
        timestamp: str | None = None,
    ) -> LawLedgerEntry:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM law_ledger WHERE entry_id = ?",
                (entry_id,) if entry_id else ("__none__",),
            ).fetchone()
            if entry_id and existing:
                row = conn.execute(
                    "SELECT * FROM law_ledger WHERE entry_id = ?",
                    (entry_id,),
                ).fetchone()
                assert row is not None
                return LawLedgerEntry.from_dict(
                    {
                        "entry_id": row["entry_id"],
                        "prev_hash": row["prev_hash"],
                        "timestamp": row["timestamp"],
                        "epoch": row["epoch"],
                        "entry_type": row["entry_type"],
                        "law_id": row["law_id"],
                        "law_hash": row["law_hash"],
                        "payload": json.loads(row["payload"] or "{}"),
                        "signed_by": row["signed_by"],
                        "signature": row["signature"],
                    }
                )

            resolved_id = entry_id or self._next_entry_id(conn, "LAW-LEDGER")
            prev_hash = self._last_entry_hash(conn)
            entry = LawLedgerEntry(
                entry_id=resolved_id,
                prev_hash=prev_hash,
                timestamp=timestamp or _now_iso(),
                epoch=epoch,
                entry_type=entry_type,
                law_id=law_id,
                law_hash=law_hash,
                payload=payload,
                signed_by=signed_by,
                signature=_sig(signed_by, resolved_id),
            )
            conn.execute(
                """
                INSERT INTO law_ledger (
                    entry_id, prev_hash, timestamp, epoch, entry_type,
                    law_id, law_hash, payload, signed_by, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.prev_hash,
                    entry.timestamp,
                    entry.epoch,
                    entry.entry_type.value,
                    entry.law_id,
                    entry.law_hash,
                    json.dumps(entry.payload, sort_keys=True),
                    entry.signed_by,
                    entry.signature,
                ),
            )
            conn.commit()
            return entry

    def upsert_law_record(self, record: LawRecord) -> LawRecord:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO law_records (
                    law_id, version, law_hash, spec_ref, status, created_at_epoch,
                    introduced_by, current_fitness, admit_threshold, reject_threshold,
                    domains, dependencies, conflicts, supersedes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(law_id) DO UPDATE SET
                    version = excluded.version,
                    law_hash = excluded.law_hash,
                    spec_ref = excluded.spec_ref,
                    status = excluded.status,
                    current_fitness = excluded.current_fitness,
                    admit_threshold = excluded.admit_threshold,
                    reject_threshold = excluded.reject_threshold,
                    domains = excluded.domains,
                    dependencies = excluded.dependencies,
                    conflicts = excluded.conflicts,
                    supersedes = excluded.supersedes
                """,
                (
                    record.law_id,
                    record.version,
                    record.law_hash,
                    record.spec_ref,
                    record.status.value,
                    record.created_at_epoch,
                    record.introduced_by,
                    record.current_fitness,
                    record.admit_threshold,
                    record.reject_threshold,
                    json.dumps(record.domains),
                    json.dumps(record.dependencies),
                    json.dumps(record.conflicts),
                    json.dumps(record.supersedes),
                ),
            )
            conn.execute(
                "DELETE FROM law_fitness_history WHERE law_id = ?",
                (record.law_id,),
            )
            for row in record.fitness_history:
                conn.execute(
                    """
                    INSERT INTO law_fitness_history (law_id, epoch, fitness, sample_size, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (record.law_id, row.epoch, row.f, row.sample_size, row.notes),
                )
            conn.commit()
        return record

    def get_law(self, law_id: str) -> LawRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM law_records WHERE law_id = ?", (law_id,)).fetchone()
            if row is None:
                return None
            history = conn.execute(
                "SELECT epoch, fitness, sample_size, notes FROM law_fitness_history "
                "WHERE law_id = ? ORDER BY epoch ASC",
                (law_id,),
            ).fetchall()
            return LawRecord(
                law_id=row["law_id"],
                version=row["version"],
                law_hash=row["law_hash"],
                spec_ref=row["spec_ref"],
                status=LawStatus(row["status"]),
                created_at_epoch=row["created_at_epoch"],
                introduced_by=row["introduced_by"],
                current_fitness=float(row["current_fitness"] or 0.0),
                admit_threshold=float(row["admit_threshold"] or DEFAULT_ADMIT_THRESHOLD),
                reject_threshold=float(row["reject_threshold"] or DEFAULT_REJECT_THRESHOLD),
                domains=json.loads(row["domains"] or "[]"),
                dependencies=json.loads(row["dependencies"] or "[]"),
                conflicts=json.loads(row["conflicts"] or "[]"),
                supersedes=json.loads(row["supersedes"] or "[]"),
                fitness_history=[
                    FitnessHistoryRow(
                        epoch=item["epoch"],
                        f=float(item["fitness"]),
                        sample_size=int(item["sample_size"]),
                        notes=str(item["notes"] or ""),
                    )
                    for item in history
                ],
            )

    def all_laws(self) -> list[LawRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT law_id FROM law_records ORDER BY created_at_epoch ASC").fetchall()
        records: list[LawRecord] = []
        for row in rows:
            record = self.get_law(str(row["law_id"]))
            if record is not None:
                records.append(record)
        return records

    def list_law_records(self) -> list[LawRecord]:
        """Alias for cockpit/API callers expecting list_law_records()."""

        return self.all_laws()

    def get_law_record(self, law_id: str) -> LawRecord | None:
        """Alias for cockpit/API callers expecting get_law_record()."""

        return self.get_law(law_id)

    def update_law_record(self, record: LawRecord) -> LawRecord:
        """Alias for cockpit/API callers expecting update_law_record()."""

        return self.upsert_law_record(record)

    def get_current_epoch(self) -> int:
        """Highest epoch recorded across law ledger entries and fitness history."""

        with self._connect() as conn:
            ledger_row = conn.execute("SELECT MAX(epoch) AS max_epoch FROM law_ledger").fetchone()
            history_row = conn.execute(
                "SELECT MAX(epoch) AS max_epoch FROM law_fitness_history"
            ).fetchone()
        ledger_epoch = int(ledger_row["max_epoch"] or 0) if ledger_row else 0
        history_epoch = int(history_row["max_epoch"] or 0) if history_row else 0
        return max(ledger_epoch, history_epoch)

    def get_lineages_for_law(self, law_id: str) -> list[Lineage]:
        """Active LCI lineages used when evaluating a law (fixture-backed for now)."""

        _ = law_id
        return lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))

    def ledger_entries(self) -> list[LawLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM law_ledger ORDER BY rowid ASC"
            ).fetchall()
        entries: list[LawLedgerEntry] = []
        for row in rows:
            entries.append(
                LawLedgerEntry.from_dict(
                    {
                        "entry_id": row["entry_id"],
                        "prev_hash": row["prev_hash"],
                        "timestamp": row["timestamp"],
                        "epoch": row["epoch"],
                        "entry_type": row["entry_type"],
                        "law_id": row["law_id"],
                        "law_hash": row["law_hash"],
                        "payload": json.loads(row["payload"] or "{}"),
                        "signed_by": row["signed_by"],
                        "signature": row["signature"],
                    }
                )
            )
        return entries


def load_founding_laws(path: Path | None = None) -> list[LawRecord]:
    target = path or FOUNDING_LAWS_FIXTURE
    payload = json.loads(target.read_text(encoding="utf-8"))
    return [LawRecord.from_dict(row) for row in payload.get("laws") or []]


def bootstrap_law_ledger(store: LawLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or LawLedgerStore()
    genesis = ledger.append_law_ledger_entry(
        entry_type=LawLedgerEntryType.LAW_GENESIS,
        law_id=LAW_LEDGER_SPEC_ID,
        law_hash=LAW_LEDGER_SPEC_HASH,
        epoch=0,
        payload=genesis_block().payload,
        signed_by="ROOT",
        entry_id=LAW_LEDGER_GENESIS_ENTRY_ID,
        timestamp="EPOCH:0:T0",
    )
    seeded: list[str] = []
    for record in load_founding_laws():
        ledger.upsert_law_record(record)
        seeded.append(record.law_id)
    return {
        "genesis_entry_id": genesis.entry_id,
        "seeded_laws": seeded,
        "law_count": len(seeded),
    }


def evaluate_law(
    record: LawRecord,
    epoch: int,
    lineages: list[Lineage],
    *,
    thresholds: dict[str, float] | None = None,
    signer: str = "kernel",
    store: LawLedgerStore | None = None,
) -> LawRecord:
    """Sovereign Selection Kernel — EIT-1 evidence-backed evaluation."""

    from src.continuity.evidence_ledger import evaluate_law_with_evidence

    return evaluate_law_with_evidence(
        record,
        epoch,
        lineages,
        thresholds=thresholds,
        signer=signer,
        law_store=store,
    )


def run_law_ledger_proof(*, store: LawLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or LawLedgerStore()
    bootstrap = bootstrap_law_ledger(ledger)
    entries = ledger.ledger_entries()
    genesis_ok = any(item.entry_id == LAW_LEDGER_GENESIS_ENTRY_ID for item in entries)
    sit = ledger.get_law("SIT-1")
    git = ledger.get_law("GIT-1")
    pit = ledger.get_law("PIT-1")
    founding_ok = (
        sit is not None
        and git is not None
        and pit is not None
        and sit.status == LawStatus.ADMITTED
        and git.status == LawStatus.ADMITTED
        and pit.status == LawStatus.EXPERIMENTAL
        and pit.current_fitness == 0.87
    )
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    pit_record = pit or load_founding_laws()[2]
    existing_eval = [
        item
        for item in ledger.ledger_entries()
        if item.entry_type == LawLedgerEntryType.LAW_EVAL
        and item.law_id == pit_record.law_id
        and int((item.payload or {}).get("epoch", -1)) == 3
    ]
    if existing_eval:
        evaluated = ledger.get_law(pit_record.law_id) or pit_record
    else:
        evaluated = evaluate_law(pit_record, epoch=3, lineages=lineages, store=ledger)
    eval_entries = [item for item in ledger.ledger_entries() if item.entry_type == LawLedgerEntryType.LAW_EVAL]
    status_entries = [
        item for item in ledger.ledger_entries() if item.entry_type == LawLedgerEntryType.LAW_STATUS_CHANGE
    ]
    last_eval = eval_entries[-1] if eval_entries else None
    payload_ok = (
        last_eval is not None
        and last_eval.payload.get("type") == "LAW_EVAL"
        and "C_cont" in (last_eval.payload.get("fitness") or {}).get("components", {})
        and bool(last_eval.payload.get("evidence_id"))
    )
    return {
        "capability_id": "LAW-LEDGER-0001",
        "genesis_ok": genesis_ok,
        "founding_laws_ok": founding_ok,
        "bootstrap": bootstrap,
        "ledger_entry_count": len(ledger.ledger_entries()),
        "law_eval_count": len(eval_entries),
        "law_status_change_count": len(status_entries),
        "pit_evaluated_fitness": round(evaluated.current_fitness, 6),
        "pit_status_after_eval": evaluated.status.value,
        "payload_ok": payload_ok,
        "passed": genesis_ok and founding_ok and payload_ok,
    }
