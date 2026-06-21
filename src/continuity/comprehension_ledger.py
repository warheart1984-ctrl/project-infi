"""Comprehension Ledger — CIT-1/CIT-2 Chi tracking parallel to Law/Evidence ledgers."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.continuity.comprehension_fitness import (
    CIT_1_CAPABILITY_ID,
    CITStrip,
    ComprehensionComponents,
    ComprehensionConfig,
    DEFAULT_DELTA_MAX,
    DEFAULT_THETA_CIT_MIN,
    UGR_CIT_1_CANONICAL_TEXT,
    UGR_CIT_2_CANONICAL_TEXT,
    build_evidence_cit_strip,
    build_law_cit_strip,
    evaluate_drift,
)


COMPREHENSION_LEDGER_SPEC_ID = "COMPREHENSION-LEDGER"
COMPREHENSION_LEDGER_GENESIS_ENTRY_ID = "COMPREHENSION-LEDGER-0000"
COMPREHENSION_LEDGER_SPEC_HASH = "hash_comprehension_ledger_spec_v1"
COMPREHENSION_LEDGER_SQL = (
    Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "comprehension_ledger.sql"
)


class ComprehensionLedgerEntryType(str, Enum):
    CHI_GENESIS = "CHI_GENESIS"
    CHI_EVAL = "CHI_EVAL"
    CHI_DRIFT_ALERT = "CHI_DRIFT_ALERT"
    CHI_THRESHOLD_BREACH = "CHI_THRESHOLD_BREACH"


@dataclass
class ComprehensionRecord:
    id: str
    object_type: str
    object_id: str
    chi: float
    components: ComprehensionComponents
    epoch: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "chi": round(self.chi, 6),
            **self.components.to_dict(),
            "epoch": self.epoch,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> ComprehensionRecord:
        return cls(
            id=str(row["id"]),
            object_type=str(row["object_type"]),
            object_id=str(row["object_id"]),
            chi=float(row["chi"]),
            components=ComprehensionComponents(
                C_loc=float(row["C_loc"]),
                C_clr=float(row["C_clr"]),
                C_cons=float(row["C_cons"]),
                C_link=float(row["C_link"]),
            ),
            epoch=int(row["epoch"]),
            created_at=str(row["created_at"]),
        )


@dataclass(frozen=True, slots=True)
class ComprehensionLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: ComprehensionLedgerEntryType
    object_type: str
    object_id: str
    payload: dict[str, Any]
    prev_hash: str | None
    entry_hash: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "epoch": self.epoch,
            "entry_type": self.entry_type.value,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "payload": dict(self.payload),
            "prev_hash": self.prev_hash,
            "hash": self.entry_hash,
            "created_at": self.created_at,
        }


def default_comprehension_ledger_path() -> Path:
    override = os.environ.get("COMPREHENSION_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "comprehension-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "comprehension-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: ComprehensionLedgerEntry) -> str:
    canonical = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def chi_record_id(object_type: str, object_id: str, epoch: int) -> str:
    return f"CHI-{object_type.upper()}-{object_id}-E{epoch}"


class ComprehensionLedgerStore:
    """SQLite-backed comprehension ledger."""

    def __init__(self, path: Path | None = None, config: ComprehensionConfig | None = None) -> None:
        self.path = path or default_comprehension_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or ComprehensionConfig()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = COMPREHENSION_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute(
            "SELECT hash FROM comprehension_ledger ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT entry_id FROM comprehension_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            ("COMPREHENSION-LEDGER-%",),
        ).fetchone()
        if row is None:
            return "COMPREHENSION-LEDGER-0001"
        tail = int(str(row["entry_id"]).split("-")[-1])
        return f"COMPREHENSION-LEDGER-{tail + 1:04d}"

    def upsert_record(self, record: ComprehensionRecord) -> ComprehensionRecord:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO comprehension_records (
                    id, object_type, object_id, chi,
                    C_loc, C_clr, C_cons, C_link, epoch, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    chi = excluded.chi,
                    C_loc = excluded.C_loc,
                    C_clr = excluded.C_clr,
                    C_cons = excluded.C_cons,
                    C_link = excluded.C_link,
                    epoch = excluded.epoch,
                    created_at = excluded.created_at
                """,
                (
                    record.id,
                    record.object_type,
                    record.object_id,
                    record.chi,
                    record.components.C_loc,
                    record.components.C_clr,
                    record.components.C_cons,
                    record.components.C_link,
                    record.epoch,
                    record.created_at,
                ),
            )
            conn.commit()
        return record

    def get_latest_record(self, object_type: str, object_id: str) -> ComprehensionRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM comprehension_records
                WHERE object_type = ? AND object_id = ?
                ORDER BY epoch DESC, rowid DESC LIMIT 1
                """,
                (object_type, object_id),
            ).fetchone()
        return ComprehensionRecord.from_row(row) if row else None

    def chi_history(self, object_type: str, object_id: str, *, limit: int = 12) -> list[float]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chi FROM comprehension_records
                WHERE object_type = ? AND object_id = ?
                ORDER BY epoch ASC, rowid ASC
                LIMIT ?
                """,
                (object_type, object_id, limit),
            ).fetchall()
        return [float(row["chi"]) for row in rows]

    def append_entry(
        self,
        *,
        entry_type: ComprehensionLedgerEntryType,
        object_type: str,
        object_id: str,
        epoch: int,
        payload: dict[str, Any],
        entry_id: str | None = None,
    ) -> ComprehensionLedgerEntry:
        with self._connect() as conn:
            resolved_id = entry_id or self._next_entry_id(conn)
            existing = conn.execute(
                "SELECT * FROM comprehension_ledger WHERE entry_id = ?",
                (resolved_id,),
            ).fetchone()
            if existing:
                return ComprehensionLedgerEntry(
                    entry_id=str(existing["entry_id"]),
                    epoch=int(existing["epoch"]),
                    entry_type=ComprehensionLedgerEntryType(str(existing["entry_type"])),
                    object_type=str(existing["object_type"]),
                    object_id=str(existing["object_id"]),
                    payload=json.loads(existing["payload_json"] or "{}"),
                    prev_hash=existing["prev_hash"],
                    entry_hash=str(existing["hash"]),
                    created_at=str(existing["created_at"]),
                )

            prev_hash = self._last_entry_hash(conn)
            created_at = _now_iso()
            draft = ComprehensionLedgerEntry(
                entry_id=resolved_id,
                epoch=epoch,
                entry_type=entry_type,
                object_type=object_type,
                object_id=object_id,
                payload=payload,
                prev_hash=prev_hash,
                entry_hash="",
                created_at=created_at,
            )
            entry_hash = _entry_hash(
                ComprehensionLedgerEntry(
                    entry_id=draft.entry_id,
                    epoch=draft.epoch,
                    entry_type=draft.entry_type,
                    object_type=draft.object_type,
                    object_id=draft.object_id,
                    payload=draft.payload,
                    prev_hash=draft.prev_hash,
                    entry_hash="",
                    created_at=draft.created_at,
                )
            )
            entry = ComprehensionLedgerEntry(
                entry_id=draft.entry_id,
                epoch=draft.epoch,
                entry_type=draft.entry_type,
                object_type=draft.object_type,
                object_id=draft.object_id,
                payload=draft.payload,
                prev_hash=draft.prev_hash,
                entry_hash=entry_hash,
                created_at=draft.created_at,
            )
            conn.execute(
                """
                INSERT INTO comprehension_ledger (
                    entry_id, epoch, entry_type, object_type, object_id,
                    payload_json, prev_hash, hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.epoch,
                    entry.entry_type.value,
                    entry.object_type,
                    entry.object_id,
                    json.dumps(entry.payload, sort_keys=True),
                    entry.prev_hash,
                    entry.entry_hash,
                    entry.created_at,
                ),
            )
            conn.commit()
            return entry

    def record_chi_eval(
        self,
        *,
        object_type: str,
        object_id: str,
        epoch: int,
        chi: float,
        components: ComprehensionComponents,
    ) -> dict[str, Any]:
        prev = self.get_latest_record(object_type, object_id)
        prev_chi = prev.chi if prev else None
        history = self.chi_history(object_type, object_id)
        drift = evaluate_drift(chi, prev_chi, cfg=self.config, history=history)

        record = ComprehensionRecord(
            id=chi_record_id(object_type, object_id, epoch),
            object_type=object_type,
            object_id=object_id,
            chi=chi,
            components=components,
            epoch=epoch,
            created_at=_now_iso(),
        )
        self.upsert_record(record)

        payload = {
            "chi": drift["chi"],
            "components": components.to_dict(),
            "thresholds": drift["thresholds"],
            "prev_chi": drift["prev_chi"],
            "delta": drift["delta"],
            "status": drift["status"],
            "warnings": drift["warnings"],
        }
        entry_type = ComprehensionLedgerEntryType.CHI_EVAL
        if drift["status"] == "breach":
            entry_type = ComprehensionLedgerEntryType.CHI_THRESHOLD_BREACH
        elif drift["status"] == "warning":
            entry_type = ComprehensionLedgerEntryType.CHI_DRIFT_ALERT

        entry = self.append_entry(
            entry_type=entry_type,
            object_type=object_type,
            object_id=object_id,
            epoch=epoch,
            payload=payload,
        )
        return {"record": record.to_dict(), "drift": drift, "entry": entry.to_dict()}

    def ledger_entries(self) -> list[ComprehensionLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM comprehension_ledger ORDER BY rowid ASC"
            ).fetchall()
        entries: list[ComprehensionLedgerEntry] = []
        for row in rows:
            entries.append(
                ComprehensionLedgerEntry(
                    entry_id=str(row["entry_id"]),
                    epoch=int(row["epoch"]),
                    entry_type=ComprehensionLedgerEntryType(str(row["entry_type"])),
                    object_type=str(row["object_type"]),
                    object_id=str(row["object_id"]),
                    payload=json.loads(row["payload_json"] or "{}"),
                    prev_hash=row["prev_hash"],
                    entry_hash=str(row["hash"]),
                    created_at=str(row["created_at"]),
                )
            )
        return entries

    def all_records(self) -> list[ComprehensionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM comprehension_records ORDER BY epoch ASC, rowid ASC"
            ).fetchall()
        return [ComprehensionRecord.from_row(row) for row in rows]


def bootstrap_comprehension_ledger(store: ComprehensionLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or ComprehensionLedgerStore()
    genesis_payload = {
        "description": "Genesis of Comprehension Ledger (UGR-CIT-1 / CIT-2)",
        "spec_ref": "UGR/CIT-1.md#v1.0.0",
        "theta_min": DEFAULT_THETA_CIT_MIN,
        "delta_max": DEFAULT_DELTA_MAX,
        "canonical_text": UGR_CIT_1_CANONICAL_TEXT[:240],
    }
    entry = ledger.append_entry(
        entry_type=ComprehensionLedgerEntryType.CHI_GENESIS,
        object_type="ledger",
        object_id=COMPREHENSION_LEDGER_SPEC_ID,
        epoch=0,
        payload=genesis_payload,
        entry_id=COMPREHENSION_LEDGER_GENESIS_ENTRY_ID,
    )
    return {"genesis_entry_id": entry.entry_id}


def evaluate_law_comprehension(
    law_record: dict[str, Any],
    *,
    epoch: int,
    evidence_id: str | None = None,
    store: ComprehensionLedgerStore | None = None,
    cfg: ComprehensionConfig | None = None,
) -> dict[str, Any]:
    ledger = store or ComprehensionLedgerStore(config=cfg)
    strip = build_law_cit_strip(law_record, evidence_id=evidence_id, epoch=epoch, cfg=cfg or ledger.config)
    result = ledger.record_chi_eval(
        object_type="law",
        object_id=strip.object_id,
        epoch=epoch,
        chi=strip.chi,
        components=strip.components,
    )
    return {"cit_strip": strip.to_dict(), **result}


def evaluate_evidence_comprehension(
    evidence: dict[str, Any],
    *,
    graph: dict[str, Any] | None = None,
    epoch: int | None = None,
    store: ComprehensionLedgerStore | None = None,
    cfg: ComprehensionConfig | None = None,
) -> dict[str, Any]:
    ledger = store or ComprehensionLedgerStore(config=cfg)
    strip = build_evidence_cit_strip(evidence, graph=graph, cfg=cfg or ledger.config)
    resolved_epoch = epoch if epoch is not None else int(evidence.get("source_epoch") or 0)
    result = ledger.record_chi_eval(
        object_type="evidence",
        object_id=strip.object_id,
        epoch=resolved_epoch,
        chi=strip.chi,
        components=strip.components,
    )
    return {"cit_strip": strip.to_dict(), **result}


def build_comprehension_health(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
    comprehension_store: ComprehensionLedgerStore | None = None,
) -> dict[str, Any]:
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    comprehension = comprehension_store or ComprehensionLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)
    bootstrap_comprehension_ledger(comprehension)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        law_dict = law.to_dict()
        evidence_id = f"EV-{law.law_id}-E{epoch}"
        ev = evidence.get_evidence(evidence_id)
        eval_result = evaluate_law_comprehension(
            law_dict,
            epoch=epoch,
            evidence_id=ev.evidence_id if ev else None,
            store=comprehension,
        )
        strip = eval_result["cit_strip"]
        drift = eval_result["drift"]
        objects.append(
            {
                "object_type": "law",
                "object_id": law.law_id,
                "chi": strip["chi"],
                "status": drift["status"],
                "warnings": drift["warnings"],
            }
        )
        for code in drift["warnings"]:
            warnings.append({"code": code, "object_id": law.law_id, "object_type": "law"})
        if strip["chi"] < comprehension.config.theta_min:
            below_threshold.append(law.law_id)

    chi_values = [item["chi"] for item in objects]
    avg_chi = round(sum(chi_values) / len(chi_values), 6) if chi_values else 0.0

    drift_detected = any(item["code"] == "CIT-DRIFT" for item in warnings)
    epoch_blocked = any(item["code"] == "CIT-BLOCK" for item in warnings)

    return {
        "avg_chi": avg_chi,
        "theta_min": comprehension.config.theta_min,
        "delta_max": comprehension.config.delta_max,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "drift_detected": drift_detected,
        "epoch_commit_blocked": epoch_blocked,
        "comprehension_ledger_tail": [entry.to_dict() for entry in comprehension.ledger_entries()[-6:]],
        "canonical": {
            "cit_1": UGR_CIT_1_CANONICAL_TEXT.split("\n")[0],
            "cit_2": UGR_CIT_2_CANONICAL_TEXT.split("\n")[0],
        },
    }


def run_cit_proof(*, store: ComprehensionLedgerStore | None = None) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    ledger = store or ComprehensionLedgerStore()
    bootstrap_comprehension_ledger(ledger)
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    health = build_comprehension_health(law_store=law_store, comprehension_store=ledger)
    pit = next((item for item in health["objects"] if item["object_id"] == "PIT-1"), None)
    return {
        "capability_id": CIT_1_CAPABILITY_ID,
        "genesis_ok": any(
            item.entry_id == COMPREHENSION_LEDGER_GENESIS_ENTRY_ID for item in ledger.ledger_entries()
        ),
        "avg_chi": health["avg_chi"],
        "pit_chi": pit["chi"] if pit else None,
        "passed": health["avg_chi"] >= ledger.config.theta_min and pit is not None,
    }
