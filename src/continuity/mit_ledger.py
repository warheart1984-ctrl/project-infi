"""MIT Ledger — UGR-MIT-1 Mu tracking parallel to Comprehension Ledger."""

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

from src.continuity.meaning_fitness import (
    MIT_1_CAPABILITY_ID,
    MeaningComponents,
    MeaningConfig,
    build_law_meaning_strip,
    compute_mu,
)


MIT_LEDGER_SPEC_ID = "MIT-LEDGER"
MIT_LEDGER_GENESIS_ENTRY_ID = "MIT-LEDGER-0000"
MIT_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "meaning_ledger.sql"


class MitLedgerEntryType(str, Enum):
    MIT_GENESIS = "MIT_GENESIS"
    MIT_EVAL = "MIT_EVAL"
    MIT_THRESHOLD_BREACH = "MIT_THRESHOLD_BREACH"


@dataclass
class MitRecord:
    id: str
    object_type: str
    object_id: str
    mu: float
    components: MeaningComponents
    epoch: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "mu": round(self.mu, 6),
            **self.components.to_dict(),
            "epoch": self.epoch,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class MitLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: MitLedgerEntryType
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


def default_mit_ledger_path() -> Path:
    override = os.environ.get("MIT_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "mit-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "mit-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: MitLedgerEntry) -> str:
    body = entry.to_dict()
    body["hash"] = ""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mit_record_id(object_type: str, object_id: str, epoch: int) -> str:
    return f"MIT-{object_type.upper()}-{object_id}-E{epoch}"


class MitLedgerStore:
    """SQLite-backed MIT invariance ledger."""

    def __init__(self, path: Path | None = None, config: MeaningConfig | None = None) -> None:
        self.path = path or default_mit_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or MeaningConfig()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = MIT_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute(
            "SELECT hash FROM meaning_ledger ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT entry_id FROM meaning_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            ("MIT-LEDGER-%",),
        ).fetchone()
        if row is None:
            return "MIT-LEDGER-0001"
        tail = int(str(row["entry_id"]).split("-")[-1])
        return f"MIT-LEDGER-{tail + 1:04d}"

    def get_latest_record(self, object_type: str, object_id: str) -> MitRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM meaning_records
                WHERE object_type = ? AND object_id = ?
                ORDER BY epoch DESC, rowid DESC LIMIT 1
                """,
                (object_type, object_id),
            ).fetchone()
        if row is None:
            return None
        return MitRecord(
            id=str(row["id"]),
            object_type=str(row["object_type"]),
            object_id=str(row["object_id"]),
            mu=float(row["mu"]),
            components=MeaningComponents(
                M_purp=float(row["M_purp"]),
                M_cons=float(row["M_cons"]),
                M_stab=float(row["M_stab"]),
                M_intent=float(row["M_intent"]),
            ),
            epoch=int(row["epoch"]),
            created_at=str(row["created_at"]),
        )

    def record_meaning(
        self,
        *,
        object_type: str,
        object_id: str,
        epoch: int,
        components: MeaningComponents,
        prev_mu: float | None = None,
    ) -> dict[str, Any]:
        mu = compute_mu(components, self.config)
        now = _now_iso()
        record = MitRecord(
            id=mit_record_id(object_type, object_id, epoch),
            object_type=object_type,
            object_id=object_id,
            mu=mu,
            components=components,
            epoch=epoch,
            created_at=now,
        )

        delta = None if prev_mu is None else round(mu - prev_mu, 6)
        status = "ok" if mu >= self.config.theta_mit else "breach"
        payload = {
            "mu": round(mu, 6),
            "components": components.to_dict(),
            "thresholds": {"theta_mit": self.config.theta_mit},
            "prev_mu": None if prev_mu is None else round(prev_mu, 6),
            "delta": delta,
            "status": status,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO meaning_records (
                    id, object_type, object_id, mu,
                    M_purp, M_cons, M_stab, M_intent, epoch, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    mu = excluded.mu,
                    M_purp = excluded.M_purp,
                    M_cons = excluded.M_cons,
                    M_stab = excluded.M_stab,
                    M_intent = excluded.M_intent,
                    epoch = excluded.epoch,
                    created_at = excluded.created_at
                """,
                (
                    record.id,
                    record.object_type,
                    record.object_id,
                    record.mu,
                    record.components.M_purp,
                    record.components.M_cons,
                    record.components.M_stab,
                    record.components.M_intent,
                    record.epoch,
                    record.created_at,
                ),
            )

            prev_hash = self._last_entry_hash(conn)
            entry_type = (
                MitLedgerEntryType.MIT_THRESHOLD_BREACH
                if status == "breach"
                else MitLedgerEntryType.MIT_EVAL
            )
            entry_id = self._next_entry_id(conn)
            draft = MitLedgerEntry(
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
            entry = MitLedgerEntry(
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
                INSERT INTO meaning_ledger (
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

        return {"record": record.to_dict(), "entry": entry.to_dict(), "mu": mu, "status": status}

    def ledger_entries(self) -> list[MitLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM meaning_ledger ORDER BY rowid ASC").fetchall()
        return [
            MitLedgerEntry(
                entry_id=str(row["entry_id"]),
                epoch=int(row["epoch"]),
                entry_type=MitLedgerEntryType(str(row["entry_type"])),
                object_type=str(row["object_type"]),
                object_id=str(row["object_id"]),
                payload=json.loads(row["payload_json"] or "{}"),
                prev_hash=row["prev_hash"],
                entry_hash=str(row["hash"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]


def bootstrap_mit_ledger(store: MitLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or MitLedgerStore()
    if any(
        item.object_id == MIT_LEDGER_SPEC_ID and item.epoch == 0
        for item in ledger.ledger_entries()
    ):
        return {"genesis_entry_id": MIT_LEDGER_GENESIS_ENTRY_ID}

    entry = ledger.record_meaning(
        object_type="ledger",
        object_id=MIT_LEDGER_SPEC_ID,
        epoch=0,
        components=MeaningComponents(M_purp=1.0, M_cons=1.0, M_stab=1.0, M_intent=1.0),
        prev_mu=None,
    )
    return {"genesis_entry_id": entry["entry"]["entry_id"]}


def evaluate_law_meaning(
    law_record: dict[str, Any],
    *,
    epoch: int,
    store: MitLedgerStore | None = None,
    cfg: MeaningConfig | None = None,
) -> dict[str, Any]:
    ledger = store or MitLedgerStore(config=cfg)
    strip = build_law_meaning_strip(law_record, cfg=cfg or ledger.config)
    prev = ledger.get_latest_record("law", strip.object_id)
    result = ledger.record_meaning(
        object_type="law",
        object_id=strip.object_id,
        epoch=epoch,
        components=strip.components,
        prev_mu=prev.mu if prev else None,
    )
    return {"meaning_strip": strip.to_dict(), **result}


def build_explain_payload(law_record: dict[str, Any]) -> dict[str, Any]:
    """Shared explain/trace/replay payload for CIT + MIT surfaces."""

    from src.continuity.comprehension_fitness import build_law_cit_strip

    strip = build_law_cit_strip(law_record, epoch=int(law_record.get("_epoch") or 0))
    meaning = build_law_meaning_strip(law_record)
    roles = list(dict.fromkeys([*strip.constitutional_role, "MIT"]))

    return {
        "law_id": law_record.get("law_id"),
        "explain": strip.explain,
        "summarize": strip.summarize,
        "why_exists": strip.why_exists,
        "what_breaks_if_removed": strip.what_breaks_if_removed,
        "constitutional_role": roles,
        "trace_links": strip.trace_links,
        "replay_hint": strip.replay_hint,
        "meaning": meaning.to_dict(),
    }


def build_mit_health(
    *,
    law_store: Any | None = None,
    mit_store: MitLedgerStore | None = None,
) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    ledger = mit_store or MitLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_mit_ledger(ledger)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        law_dict = law.to_dict()
        law_dict["_epoch"] = epoch
        result = evaluate_law_meaning(law_dict, epoch=epoch, store=ledger)
        status = result["status"]
        mu = result["mu"]
        objects.append(
            {
                "object_type": "law",
                "object_id": law.law_id,
                "mu": mu,
                "status": status,
            }
        )
        if status == "breach":
            below_threshold.append(law.law_id)
            warnings.append({"code": "MIT-LOW", "object_id": law.law_id, "object_type": "law"})

    mu_values = [item["mu"] for item in objects]
    avg_mu = round(sum(mu_values) / len(mu_values), 6) if mu_values else 0.0

    return {
        "avg_mu": avg_mu,
        "theta_mit": ledger.config.theta_mit,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "meaning_ledger_tail": [entry.to_dict() for entry in ledger.ledger_entries()[-6:]],
    }


def run_mit_proof(*, store: MitLedgerStore | None = None) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    ledger = store or MitLedgerStore()
    bootstrap_mit_ledger(ledger)
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    pit = law_store.get_law("PIT-1")
    assert pit is not None
    result = evaluate_law_meaning(pit.to_dict(), epoch=3, store=ledger)
    return {
        "capability_id": MIT_1_CAPABILITY_ID,
        "mu": result["mu"],
        "passed": result["mu"] >= ledger.config.theta_mit,
    }
