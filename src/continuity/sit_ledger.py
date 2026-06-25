"""SIT Ledger — UGR-SIT-1 Sigma tracking parallel to MIT/CIT ledgers."""

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

from src.continuity.structural_fitness import (
    SIT_1_CAPABILITY_ID,
    StructuralComponents,
    StructuralConfig,
    UGR_SIT_1_CANONICAL_TEXT,
    build_law_structural_strip,
    compute_sigma,
)


SIT_LEDGER_SPEC_ID = "SIT-LEDGER"
SIT_LEDGER_GENESIS_ENTRY_ID = "SIT-LEDGER-0000"
SIT_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "sit_ledger.sql"


class SitLedgerEntryType(str, Enum):
    SIT_GENESIS = "SIT_GENESIS"
    SIT_EVAL = "SIT_EVAL"
    SIT_THRESHOLD_BREACH = "SIT_THRESHOLD_BREACH"


@dataclass
class SitRecord:
    id: str
    object_type: str
    object_id: str
    sigma: float
    components: StructuralComponents
    epoch: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "sigma": round(self.sigma, 6),
            **self.components.to_dict(),
            "epoch": self.epoch,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class SitLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: SitLedgerEntryType
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


def default_sit_ledger_path() -> Path:
    override = os.environ.get("SIT_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "sit-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "sit-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: SitLedgerEntry) -> str:
    body = entry.to_dict()
    body["hash"] = ""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sit_record_id(object_type: str, object_id: str, epoch: int) -> str:
    return f"SIG-{object_type.upper()}-{object_id}-E{epoch}"


class SitLedgerStore:
    def __init__(self, path: Path | None = None, config: StructuralConfig | None = None) -> None:
        self.path = path or default_sit_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or StructuralConfig()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = SIT_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT hash FROM sit_ledger ORDER BY rowid DESC LIMIT 1").fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT entry_id FROM sit_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            ("SIT-LEDGER-%",),
        ).fetchone()
        if row is None:
            return "SIT-LEDGER-0001"
        tail = int(str(row["entry_id"]).split("-")[-1])
        return f"SIT-LEDGER-{tail + 1:04d}"

    def get_latest_record(self, object_type: str, object_id: str) -> SitRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM structural_records
                WHERE object_type = ? AND object_id = ?
                ORDER BY epoch DESC, rowid DESC LIMIT 1
                """,
                (object_type, object_id),
            ).fetchone()
        if row is None:
            return None
        return SitRecord(
            id=str(row["id"]),
            object_type=str(row["object_type"]),
            object_id=str(row["object_id"]),
            sigma=float(row["sigma"]),
            components=StructuralComponents(
                S_equiv=float(row["S_equiv"]),
                S_indep=float(row["S_indep"]),
                S_recover=float(row["S_recover"]),
                S_trace=float(row["S_trace"]),
            ),
            epoch=int(row["epoch"]),
            created_at=str(row["created_at"]),
        )

    def record_structure(
        self,
        *,
        object_type: str,
        object_id: str,
        epoch: int,
        components: StructuralComponents,
        prev_sigma: float | None = None,
    ) -> dict[str, Any]:
        sigma = compute_sigma(components, self.config)
        now = _now_iso()
        record = SitRecord(
            id=sit_record_id(object_type, object_id, epoch),
            object_type=object_type,
            object_id=object_id,
            sigma=sigma,
            components=components,
            epoch=epoch,
            created_at=now,
        )

        delta = None if prev_sigma is None else round(sigma - prev_sigma, 6)
        status = "ok" if sigma >= self.config.theta_sit else "breach"
        payload = {
            "sigma": round(sigma, 6),
            "components": components.to_dict(),
            "thresholds": {"theta_sit": self.config.theta_sit},
            "prev_sigma": None if prev_sigma is None else round(prev_sigma, 6),
            "delta": delta,
            "status": status,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO structural_records (
                    id, object_type, object_id, sigma,
                    S_equiv, S_indep, S_recover, S_trace, epoch, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sigma = excluded.sigma,
                    S_equiv = excluded.S_equiv,
                    S_indep = excluded.S_indep,
                    S_recover = excluded.S_recover,
                    S_trace = excluded.S_trace,
                    epoch = excluded.epoch,
                    created_at = excluded.created_at
                """,
                (
                    record.id,
                    record.object_type,
                    record.object_id,
                    record.sigma,
                    record.components.S_equiv,
                    record.components.S_indep,
                    record.components.S_recover,
                    record.components.S_trace,
                    record.epoch,
                    record.created_at,
                ),
            )

            prev_hash = self._last_entry_hash(conn)
            entry_type = (
                SitLedgerEntryType.SIT_THRESHOLD_BREACH
                if status == "breach"
                else SitLedgerEntryType.SIT_EVAL
            )
            entry_id = self._next_entry_id(conn)
            draft = SitLedgerEntry(
                entry_id=entry_id,
                epoch=epoch,
                entry_type=entry_type,
                object_type=object_type,
                object_id=object_id,
                payload=payload,
                prev_hash=prev_hash,
                entry_hash="",
                created_at=now,
            )
            entry_hash = _entry_hash(draft)
            entry = SitLedgerEntry(
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
                INSERT INTO sit_ledger (
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

        return {"record": record.to_dict(), "entry": entry.to_dict(), "sigma": sigma, "status": status}

    def ledger_entries(self) -> list[SitLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM sit_ledger ORDER BY rowid ASC").fetchall()
        return [
            SitLedgerEntry(
                entry_id=str(row["entry_id"]),
                epoch=int(row["epoch"]),
                entry_type=SitLedgerEntryType(str(row["entry_type"])),
                object_type=str(row["object_type"]),
                object_id=str(row["object_id"]),
                payload=json.loads(row["payload_json"] or "{}"),
                prev_hash=row["prev_hash"],
                entry_hash=str(row["hash"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]


def bootstrap_sit_ledger(store: SitLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or SitLedgerStore()
    if any(
        item.object_id == SIT_LEDGER_SPEC_ID and item.epoch == 0
        for item in ledger.ledger_entries()
    ):
        return {"genesis_entry_id": SIT_LEDGER_GENESIS_ENTRY_ID}

    entry = ledger.record_structure(
        object_type="ledger",
        object_id=SIT_LEDGER_SPEC_ID,
        epoch=0,
        components=StructuralComponents(S_equiv=1.0, S_indep=1.0, S_recover=1.0, S_trace=1.0),
        prev_sigma=None,
    )
    return {"genesis_entry_id": entry["entry"]["entry_id"]}


def evaluate_law_structure(
    law_record: dict[str, Any],
    *,
    epoch: int,
    lineages: list[Any] | None = None,
    graph: dict[str, Any] | None = None,
    evidence_present: bool = False,
    store: SitLedgerStore | None = None,
    cfg: StructuralConfig | None = None,
) -> dict[str, Any]:
    ledger = store or SitLedgerStore(config=cfg)
    strip = build_law_structural_strip(
        law_record,
        lineage_count=len(lineages or []),
        graph=graph,
        evidence_present=evidence_present,
        cfg=cfg or ledger.config,
    )
    prev = ledger.get_latest_record("law", strip.object_id)
    result = ledger.record_structure(
        object_type="law",
        object_id=strip.object_id,
        epoch=epoch,
        components=strip.components,
        prev_sigma=prev.sigma if prev else None,
    )
    return {"sit_strip": strip.to_dict(), **result}


def build_sit_health(
    *,
    law_store: Any | None = None,
    evidence_store: Any | None = None,
    sit_store: SitLedgerStore | None = None,
) -> dict[str, Any]:
    from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger, evidence_id_for
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    ledger = sit_store or SitLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)
    bootstrap_sit_ledger(ledger)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        law_dict = law.to_dict()
        lineages = laws.get_lineages_for_law(law.law_id)
        evidence_id = evidence_id_for(law.law_id, epoch)
        ev = evidence.get_evidence(evidence_id)
        graph = evidence.get_lineage_graph(evidence_id) if ev else None
        result = evaluate_law_structure(
            law_dict,
            epoch=epoch,
            lineages=lineages,
            graph=graph,
            evidence_present=ev is not None,
            store=ledger,
        )
        status = result["status"]
        sigma = result["sigma"]
        objects.append(
            {
                "object_type": "law",
                "object_id": law.law_id,
                "sigma": sigma,
                "status": status,
            }
        )
        if status == "breach":
            below_threshold.append(law.law_id)
            warnings.append({"code": "SIT-LOW", "object_id": law.law_id, "object_type": "law"})

    sigma_values = [item["sigma"] for item in objects]
    avg_sigma = round(sum(sigma_values) / len(sigma_values), 6) if sigma_values else 0.0

    return {
        "avg_sigma": avg_sigma,
        "theta_sit": ledger.config.theta_sit,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "epoch_commit_blocked": len(below_threshold) > 0,
        "sit_ledger_tail": [entry.to_dict() for entry in ledger.ledger_entries()[-6:]],
        "canonical": UGR_SIT_1_CANONICAL_TEXT.split("\n")[0],
    }


def run_sit_proof(*, store: SitLedgerStore | None = None) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    ledger = store or SitLedgerStore()
    bootstrap_sit_ledger(ledger)
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    health = build_sit_health(law_store=law_store, sit_store=ledger)
    sit = next((item for item in health["objects"] if item["object_id"] == "SIT-1"), None)
    return {
        "capability_id": SIT_1_CAPABILITY_ID,
        "avg_sigma": health["avg_sigma"],
        "sit_sigma": sit["sigma"] if sit else None,
        "passed": health["avg_sigma"] >= ledger.config.theta_sit and sit is not None,
    }
