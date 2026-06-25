"""GIT Ledger — UGR-GIT-1 Lambda tracking parallel to SIT/MIT ledgers."""

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

from src.continuity.git_fitness import (
    DEFAULT_THETA_GIT,
    GIT_1_CAPABILITY_ID,
    GenerativeComponents,
    GenerativeConfig,
    UGR_GIT_1_CANONICAL_TEXT,
    build_law_generative_strip,
    compute_lambda,
)


GIT_LEDGER_SPEC_ID = "GIT-LEDGER"
GIT_LEDGER_GENESIS_ENTRY_ID = "GIT-LEDGER-0000"
GIT_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "git_ledger.sql"


class GitLedgerEntryType(str, Enum):
    GIT_GENESIS = "GIT_GENESIS"
    GIT_EVAL = "GIT_EVAL"
    GIT_THRESHOLD_BREACH = "GIT_THRESHOLD_BREACH"


@dataclass
class GitRecord:
    id: str
    object_type: str
    object_id: str
    lambda_value: float
    components: GenerativeComponents
    epoch: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "lambda": round(self.lambda_value, 6),
            **self.components.to_dict(),
            "epoch": self.epoch,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class GitLedgerEntry:
    entry_id: str
    epoch: int
    entry_type: GitLedgerEntryType
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


def default_git_ledger_path() -> Path:
    override = os.environ.get("GIT_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "git-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "git-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _entry_hash(entry: GitLedgerEntry) -> str:
    body = entry.to_dict()
    body["hash"] = ""
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def git_record_id(object_type: str, object_id: str, epoch: int) -> str:
    return f"LAM-{object_type.upper()}-{object_id}-E{epoch}"


class GitLedgerStore:
    def __init__(self, path: Path | None = None, config: GenerativeConfig | None = None) -> None:
        self.path = path or default_git_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.config = config or GenerativeConfig()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = GIT_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute("SELECT hash FROM git_ledger ORDER BY rowid DESC LIMIT 1").fetchone()
        return str(row["hash"]) if row else None

    def _next_entry_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT entry_id FROM git_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            ("GIT-LEDGER-%",),
        ).fetchone()
        if row is None:
            return "GIT-LEDGER-0001"
        tail = int(str(row["entry_id"]).split("-")[-1])
        return f"GIT-LEDGER-{tail + 1:04d}"

    def get_latest_record(self, object_type: str, object_id: str) -> GitRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM generative_records
                WHERE object_type = ? AND object_id = ?
                ORDER BY epoch DESC, rowid DESC LIMIT 1
                """,
                (object_type, object_id),
            ).fetchone()
        if row is None:
            return None
        return GitRecord(
            id=str(row["id"]),
            object_type=str(row["object_type"]),
            object_id=str(row["object_id"]),
            lambda_value=float(row["lambda"]),
            components=GenerativeComponents(
                G_recover=float(row["G_recover"]),
                G_cross=float(row["G_cross"]),
                G_intra=float(row["G_intra"]),
                G_trace=float(row["G_trace"]),
            ),
            epoch=int(row["epoch"]),
            created_at=str(row["created_at"]),
        )

    def record_generative(
        self,
        *,
        object_type: str,
        object_id: str,
        epoch: int,
        components: GenerativeComponents,
        generative_law: str = "",
        prev_lambda: float | None = None,
    ) -> dict[str, Any]:
        lambda_value = compute_lambda(components, self.config)
        now = _now_iso()
        record = GitRecord(
            id=git_record_id(object_type, object_id, epoch),
            object_type=object_type,
            object_id=object_id,
            lambda_value=lambda_value,
            components=components,
            epoch=epoch,
            created_at=now,
        )

        delta = None if prev_lambda is None else round(lambda_value - prev_lambda, 6)
        status = "ok" if lambda_value >= self.config.theta_git else "breach"
        payload = {
            "lambda": round(lambda_value, 6),
            "generative_law": generative_law,
            "components": components.to_dict(),
            "thresholds": {"theta_git": self.config.theta_git},
            "prev_lambda": None if prev_lambda is None else round(prev_lambda, 6),
            "delta": delta,
            "status": status,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO generative_records (
                    id, object_type, object_id, lambda,
                    G_recover, G_cross, G_intra, G_trace, epoch, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    lambda = excluded.lambda,
                    G_recover = excluded.G_recover,
                    G_cross = excluded.G_cross,
                    G_intra = excluded.G_intra,
                    G_trace = excluded.G_trace,
                    epoch = excluded.epoch,
                    created_at = excluded.created_at
                """,
                (
                    record.id,
                    record.object_type,
                    record.object_id,
                    record.lambda_value,
                    record.components.G_recover,
                    record.components.G_cross,
                    record.components.G_intra,
                    record.components.G_trace,
                    record.epoch,
                    record.created_at,
                ),
            )

            prev_hash = self._last_entry_hash(conn)
            entry_type = (
                GitLedgerEntryType.GIT_THRESHOLD_BREACH
                if status == "breach"
                else GitLedgerEntryType.GIT_EVAL
            )
            entry_id = self._next_entry_id(conn)
            draft = GitLedgerEntry(
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
            entry = GitLedgerEntry(
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
                INSERT INTO git_ledger (
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

        return {
            "record": record.to_dict(),
            "entry": entry.to_dict(),
            "lambda": lambda_value,
            "status": status,
        }

    def ledger_entries(self) -> list[GitLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM git_ledger ORDER BY rowid ASC").fetchall()
        return [
            GitLedgerEntry(
                entry_id=str(row["entry_id"]),
                epoch=int(row["epoch"]),
                entry_type=GitLedgerEntryType(str(row["entry_type"])),
                object_type=str(row["object_type"]),
                object_id=str(row["object_id"]),
                payload=json.loads(row["payload_json"] or "{}"),
                prev_hash=row["prev_hash"],
                entry_hash=str(row["hash"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]


def bootstrap_git_ledger(store: GitLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or GitLedgerStore()
    if any(
        item.object_id == GIT_LEDGER_SPEC_ID and item.epoch == 0
        for item in ledger.ledger_entries()
    ):
        return {"genesis_entry_id": GIT_LEDGER_GENESIS_ENTRY_ID}

    entry = ledger.record_generative(
        object_type="ledger",
        object_id=GIT_LEDGER_SPEC_ID,
        epoch=0,
        components=GenerativeComponents(G_recover=1.0, G_cross=1.0, G_intra=1.0, G_trace=1.0),
        generative_law="C-Chain Evolution Law",
        prev_lambda=None,
    )
    return {"genesis_entry_id": entry["entry"]["entry_id"]}


def evaluate_law_generative(
    law_record: dict[str, Any],
    *,
    epoch: int,
    lineages: list[Any] | None = None,
    store: GitLedgerStore | None = None,
    cfg: GenerativeConfig | None = None,
) -> dict[str, Any]:
    ledger = store or GitLedgerStore(config=cfg)
    strip = build_law_generative_strip(law_record, lineages=lineages, cfg=cfg or ledger.config)
    prev = ledger.get_latest_record("law", strip.object_id)
    result = ledger.record_generative(
        object_type="law",
        object_id=strip.object_id,
        epoch=epoch,
        components=strip.components,
        generative_law=strip.generative_law,
        prev_lambda=prev.lambda_value if prev else None,
    )
    return {"git_strip": strip.to_dict(), **result}


def build_git_health(
    *,
    law_store: Any | None = None,
    git_store: GitLedgerStore | None = None,
) -> dict[str, Any]:
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    laws = law_store or LawLedgerStore()
    ledger = git_store or GitLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_git_ledger(ledger)

    epoch = laws.get_current_epoch()
    objects: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    below_threshold: list[str] = []

    for law in laws.all_laws():
        law_dict = law.to_dict()
        lineages = laws.get_lineages_for_law(law.law_id)
        result = evaluate_law_generative(law_dict, epoch=epoch, lineages=lineages, store=ledger)
        status = result["status"]
        lambda_value = result["lambda"]
        objects.append(
            {
                "object_type": "law",
                "object_id": law.law_id,
                "lambda": lambda_value,
                "status": status,
            }
        )
        if status == "breach":
            below_threshold.append(law.law_id)
            warnings.append({"code": "GIT-LOW", "object_id": law.law_id, "object_type": "law"})

    lambda_values = [item["lambda"] for item in objects]
    avg_lambda = round(sum(lambda_values) / len(lambda_values), 6) if lambda_values else 0.0

    return {
        "avg_lambda": avg_lambda,
        "theta_git": ledger.config.theta_git,
        "objects": objects,
        "below_threshold": below_threshold,
        "warnings": warnings,
        "epoch_commit_blocked": len(below_threshold) > 0,
        "git_ledger_tail": [entry.to_dict() for entry in ledger.ledger_entries()[-6:]],
        "canonical": UGR_GIT_1_CANONICAL_TEXT.split("\n")[0],
    }


def run_git_fitness_proof(*, store: GitLedgerStore | None = None) -> dict[str, Any]:
    from src.continuity.generative_law import run_git_1_proof
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    ledger = store or GitLedgerStore()
    bootstrap_git_ledger(ledger)
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    git1 = run_git_1_proof()
    health = build_git_health(law_store=law_store, git_store=ledger)
    git_law = next((item for item in health["objects"] if item["object_id"] == "GIT-1"), None)
    return {
        "capability_id": GIT_1_CAPABILITY_ID,
        "git1_passed": git1.get("passed", False),
        "avg_lambda": health["avg_lambda"],
        "git_lambda": git_law["lambda"] if git_law else None,
        "passed": git1.get("passed", False)
        and health["avg_lambda"] >= DEFAULT_THETA_GIT
        and git_law is not None,
    }
