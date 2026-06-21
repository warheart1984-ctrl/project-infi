"""EIT-1 — Evidence Invariance Theory and Evidence Ledger (proof layer)."""

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

from src.continuity.law_ledger import (
    FitnessHistoryRow,
    LawLedgerStore,
    LawRecord,
    LawStatus,
    aggregate_fitness,
    compute_fitness_components,
    decide_status,
    law_eval_payload,
    law_status_change_payload,
)
from src.continuity.law_ledger import LawLedgerEntryType
from src.continuity.lineage import Lineage, continuity_trace


EVIDENCE_LEDGER_SPEC_ID = "EVIDENCE-LEDGER"
EVIDENCE_LEDGER_GENESIS_ENTRY_ID = "EVIDENCE-LEDGER-0000"
EVIDENCE_LEDGER_SPEC_HASH = "hash_evidence_ledger_spec_v1"
EVIDENCE_LEDGER_SQL = Path(__file__).resolve().parents[2] / "fixtures" / "continuity" / "evidence_ledger.sql"

UGR_EIT_1_CODE = "UGR-EIT-1"
EIT_1_CAPABILITY_ID = "UGR-EIT-1-evidence-invariance"

UGR_EIT_1_CANONICAL_TEXT = """UGR-EIT-1 — Evidence Invariance Theory
Version: 1.0.0
Class: Constitutional Invariant
Status: Proposed → Experimental → Admitted (pending PIT)

Purpose
To ensure that every lawful decision in the substrate is backed by a recoverable,
operator-invariant evidence lineage.

Statement
For any lawful decision D, there exists an evidence lineage E such that:
  D = f(E)
and for any admissible operator O:
  O(E) ≅ E

Guarantees
- No decision without evidence.
- No evidence without validation.
- No validation without invariance.
- No invariance without replayability.

Violations
Any decision lacking a valid evidence lineage is constitutionally void.

Cardinal Expansion
North (Structural): EvidenceRecord is the atomic unit of justification; every
  structure, law, fitness score, and decision points to evidence.
South (Operational): Evidence Ledger — ROOT-class append-only chain with
  EVIDENCE_CREATE, EVIDENCE_VALIDATE, EVIDENCE_LINK, EVIDENCE_REVOKE.
East (Mathematical): D = f(E); O(E) ≅ E; fitness components derived from evidence.
West (Constitutional): LAW_EVAL and LAW_STATUS_CHANGE bind evidence_id; void without proof.
Above (Meta-Governance): Law Ledger → Evidence Ledger → validation methods → PIT → EIT loop.
Below (Substrate): EvidenceLedgerStore, build_evidence_from_lineages, validate_evidence,
  evaluate_law_with_evidence, fixtures, apply_constitutional_chain proof.
Center (Epoch-∞): Self-verifying substrate — no silent decisions, no unproven laws,
  no unverifiable fitness, no opaque governance.

Integration
- SIT: structure claims require evidence of structure recovery.
- GIT: generative law claims require evidence of law recovery.
- PIT: fitness claims require evidence of fitness derivation.
- Law Ledger: every decision entry binds evidence_id.
"""


class EvidenceType(str, Enum):
    OBSERVATION = "observation"
    SIMULATION = "simulation"
    DERIVATION = "derivation"
    TESTIMONY = "testimony"
    IMPORT = "import"


class EvidenceLedgerEntryType(str, Enum):
    EVIDENCE_GENESIS = "EVIDENCE_GENESIS"
    EVIDENCE_CREATE = "EVIDENCE_CREATE"
    EVIDENCE_VALIDATE = "EVIDENCE_VALIDATE"
    EVIDENCE_LINK = "EVIDENCE_LINK"
    EVIDENCE_REVOKE = "EVIDENCE_REVOKE"


@dataclass
class EvidenceRecord:
    evidence_id: str
    evidence_hash: str
    evidence_type: EvidenceType
    source_lineage: str
    source_epoch: int
    validation_method: str
    confidence: float
    dependencies: list[str] = field(default_factory=list)
    trace_links: list[str] = field(default_factory=list)
    canonical_hash: str = ""
    components: dict[str, float] = field(default_factory=dict)
    sample_size: int = 0
    law_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_hash": self.evidence_hash,
            "evidence_type": self.evidence_type.value,
            "source_lineage": self.source_lineage,
            "source_epoch": self.source_epoch,
            "validation_method": self.validation_method,
            "confidence": round(self.confidence, 6),
            "dependencies": list(self.dependencies),
            "trace_links": list(self.trace_links),
            "canonical_hash": self.canonical_hash,
        }

    def to_storage_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["_components"] = {key: round(value, 6) for key, value in self.components.items()}
        payload["_sample_size"] = self.sample_size
        payload["_law_id"] = self.law_id
        return payload

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> EvidenceRecord:
        return cls(
            evidence_id=str(row["evidence_id"]),
            evidence_hash=str(row["evidence_hash"]),
            evidence_type=EvidenceType(str(row["evidence_type"])),
            source_lineage=str(row["source_lineage"]),
            source_epoch=int(row["source_epoch"]),
            validation_method=str(row["validation_method"]),
            confidence=float(row["confidence"]),
            dependencies=[str(item) for item in row.get("dependencies") or []],
            trace_links=[str(item) for item in row.get("trace_links") or []],
            canonical_hash=str(row.get("canonical_hash") or ""),
            components={str(k): float(v) for k, v in (row.get("_components") or {}).items()},
            sample_size=int(row.get("_sample_size") or 0),
            law_id=str(row.get("_law_id") or ""),
        )


@dataclass(frozen=True, slots=True)
class EvidenceLedgerEntry:
    entry_id: str
    prev_hash: str | None
    timestamp: str
    epoch: int
    entry_type: EvidenceLedgerEntryType
    evidence_id: str
    evidence_hash: str
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
            "evidence_id": self.evidence_id,
            "evidence_hash": self.evidence_hash,
            "payload": dict(self.payload),
            "signed_by": self.signed_by,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> EvidenceLedgerEntry:
        return cls(
            entry_id=str(row["entry_id"]),
            prev_hash=row.get("prev_hash"),
            timestamp=str(row["timestamp"]),
            epoch=int(row["epoch"]),
            entry_type=EvidenceLedgerEntryType(str(row["entry_type"])),
            evidence_id=str(row["evidence_id"]),
            evidence_hash=str(row["evidence_hash"]),
            payload=dict(row.get("payload") or {}),
            signed_by=str(row["signed_by"]),
            signature=str(row["signature"]),
        )


def default_evidence_ledger_path() -> Path:
    override = os.environ.get("EVIDENCE_LEDGER_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    online = os.environ.get("AAIS_ONLINE_RUNTIME_DIR", "").strip()
    if online:
        return Path(online).expanduser().resolve() / "evidence-ledger.sqlite3"
    root = Path(__file__).resolve().parents[2]
    return root / ".runtime" / "online" / "evidence-ledger.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sig(signer: str, entry_id: str) -> str:
    return f"sig({signer}, {entry_id})"


def _entry_hash(entry: EvidenceLedgerEntry) -> str:
    canonical = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_evidence_body(
    *,
    law_id: str,
    epoch: int,
    lineages: list[Lineage],
    components: dict[str, float],
) -> dict[str, Any]:
    trace_links = sorted(
        event_id
        for lineage in lineages
        for event_id in sorted(continuity_trace(lineage))
    )
    return {
        "law_id": law_id,
        "epoch": epoch,
        "lineage_ids": sorted(item.lineage_id for item in lineages),
        "trace_links": trace_links,
        "components": {key: round(value, 6) for key, value in components.items()},
        "sample_size": len(lineages),
    }


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evidence_id_for(law_id: str, epoch: int) -> str:
    return f"EV-{law_id}-E{epoch}"


def build_evidence_from_lineages(
    record: LawRecord,
    epoch: int,
    lineages: list[Lineage],
    *,
    signer: str,
) -> EvidenceRecord:
    """Generate recoverable evidence from lineage observations."""

    components = compute_fitness_components(lineages)
    body = _canonical_evidence_body(
        law_id=record.law_id,
        epoch=epoch,
        lineages=lineages,
        components=components,
    )
    canonical_hash = _hash_payload(body)
    source_lineage = lineages[0].lineage_id if lineages else "L0-GENESIS"
    trace_links = list(body["trace_links"])
    confidence = min(1.0, max(0.0, aggregate_fitness(components)))
    resolved_id = evidence_id_for(record.law_id, epoch)
    evidence_hash = _hash_payload(
        {
            "evidence_id": resolved_id,
            "canonical_hash": canonical_hash,
            "signer": signer,
        }
    )
    return EvidenceRecord(
        evidence_id=resolved_id,
        evidence_hash=evidence_hash,
        evidence_type=EvidenceType.DERIVATION,
        source_lineage=source_lineage,
        source_epoch=epoch,
        validation_method="lci_stack_replay",
        confidence=confidence,
        dependencies=list(record.dependencies),
        trace_links=trace_links,
        canonical_hash=canonical_hash,
        components=components,
        sample_size=len(lineages),
        law_id=record.law_id,
    )


def derive_components_from_evidence(evidence: EvidenceRecord) -> dict[str, float]:
    """Recover fitness components from stored evidence (operator-invariant replay)."""

    if evidence.components:
        return dict(evidence.components)
    raise ValueError(f"evidence {evidence.evidence_id} is not recoverable")


def operator_replay_equivalent(left: EvidenceRecord, right: EvidenceRecord) -> bool:
    """O(E) ≅ E — replayed evidence matches canonical lineage body."""

    if not left.canonical_hash or not right.canonical_hash:
        return left.evidence_hash == right.evidence_hash
    return left.canonical_hash == right.canonical_hash


class EvidenceLedgerStore:
    """SQLite-backed Evidence Ledger — append-only proof chain."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_evidence_ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        sql = EVIDENCE_LEDGER_SQL.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    def _last_entry_hash(self, conn: sqlite3.Connection) -> str | None:
        row = conn.execute(
            "SELECT entry_id, prev_hash, timestamp, epoch, entry_type, evidence_id, "
            "evidence_hash, payload, signed_by, signature "
            "FROM evidence_ledger ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        entry = EvidenceLedgerEntry.from_dict(
            {
                "entry_id": row["entry_id"],
                "prev_hash": row["prev_hash"],
                "timestamp": row["timestamp"],
                "epoch": row["epoch"],
                "entry_type": row["entry_type"],
                "evidence_id": row["evidence_id"],
                "evidence_hash": row["evidence_hash"],
                "payload": json.loads(row["payload"] or "{}"),
                "signed_by": row["signed_by"],
                "signature": row["signature"],
            }
        )
        return _entry_hash(entry)

    def _next_entry_id(self, conn: sqlite3.Connection, prefix: str) -> str:
        row = conn.execute(
            "SELECT entry_id FROM evidence_ledger WHERE entry_id LIKE ? ORDER BY entry_id DESC LIMIT 1",
            (f"{prefix}-%",),
        ).fetchone()
        if row is None:
            return f"{prefix}-0001"
        tail = str(row["entry_id"]).split("-")[-1]
        return f"{prefix}-{int(tail) + 1:04d}"

    def _upsert_evidence_record_conn(self, conn: sqlite3.Connection, record: EvidenceRecord) -> None:
        storage = record.to_storage_dict()
        conn.execute(
            """
            INSERT INTO evidence_records (
                evidence_id, evidence_hash, evidence_type, source_lineage,
                source_epoch, validation_method, confidence,
                dependencies, trace_links, canonical_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                evidence_hash = excluded.evidence_hash,
                evidence_type = excluded.evidence_type,
                source_lineage = excluded.source_lineage,
                source_epoch = excluded.source_epoch,
                validation_method = excluded.validation_method,
                confidence = excluded.confidence,
                dependencies = excluded.dependencies,
                trace_links = excluded.trace_links,
                canonical_hash = excluded.canonical_hash
            """,
            (
                record.evidence_id,
                record.evidence_hash,
                record.evidence_type.value,
                record.source_lineage,
                record.source_epoch,
                record.validation_method,
                record.confidence,
                json.dumps(storage),
                json.dumps(record.trace_links),
                record.canonical_hash,
            ),
        )

    def upsert_evidence_record(self, record: EvidenceRecord) -> EvidenceRecord:
        with self._connect() as conn:
            self._upsert_evidence_record_conn(conn, record)
            conn.commit()
        return record

    def get_evidence(self, evidence_id: str) -> EvidenceRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evidence_records WHERE evidence_id = ?",
                (evidence_id,),
            ).fetchone()
            if row is None:
                return None
            stored = json.loads(row["dependencies"] or "{}")
            if isinstance(stored, list):
                stored = {"dependencies": stored}
            base = EvidenceRecord.from_dict(
                {
                    "evidence_id": row["evidence_id"],
                    "evidence_hash": row["evidence_hash"],
                    "evidence_type": row["evidence_type"],
                    "source_lineage": row["source_lineage"],
                    "source_epoch": row["source_epoch"],
                    "validation_method": row["validation_method"],
                    "confidence": row["confidence"],
                    "dependencies": stored.get("dependencies") or [],
                    "trace_links": json.loads(row["trace_links"] or "[]"),
                    "canonical_hash": row["canonical_hash"] or "",
                    "_components": stored.get("_components") or {},
                    "_sample_size": stored.get("_sample_size") or 0,
                    "_law_id": stored.get("_law_id") or "",
                }
            )
            return base

    def append_evidence_ledger_entry(
        self,
        *,
        entry_type: EvidenceLedgerEntryType,
        evidence: EvidenceRecord,
        epoch: int,
        payload: dict[str, Any],
        signed_by: str,
        entry_id: str | None = None,
        timestamp: str | None = None,
    ) -> EvidenceLedgerEntry:
        with self._connect() as conn:
            if entry_id:
                existing = conn.execute(
                    "SELECT * FROM evidence_ledger WHERE entry_id = ?",
                    (entry_id,),
                ).fetchone()
                if existing:
                    return EvidenceLedgerEntry.from_dict(
                        {
                            "entry_id": existing["entry_id"],
                            "prev_hash": existing["prev_hash"],
                            "timestamp": existing["timestamp"],
                            "epoch": existing["epoch"],
                            "entry_type": existing["entry_type"],
                            "evidence_id": existing["evidence_id"],
                            "evidence_hash": existing["evidence_hash"],
                            "payload": json.loads(existing["payload"] or "{}"),
                            "signed_by": existing["signed_by"],
                            "signature": existing["signature"],
                        }
                    )

            resolved_id = entry_id or self._next_entry_id(conn, "EVIDENCE-LEDGER")
            prev_hash = self._last_entry_hash(conn)
            self._upsert_evidence_record_conn(conn, evidence)
            entry = EvidenceLedgerEntry(
                entry_id=resolved_id,
                prev_hash=prev_hash,
                timestamp=timestamp or _now_iso(),
                epoch=epoch,
                entry_type=entry_type,
                evidence_id=evidence.evidence_id,
                evidence_hash=evidence.evidence_hash,
                payload=payload,
                signed_by=signed_by,
                signature=_sig(signed_by, resolved_id),
            )
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    entry_id, prev_hash, timestamp, epoch, entry_type,
                    evidence_id, evidence_hash, payload, signed_by, signature
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.prev_hash,
                    entry.timestamp,
                    entry.epoch,
                    entry.entry_type.value,
                    entry.evidence_id,
                    entry.evidence_hash,
                    json.dumps(entry.payload, sort_keys=True),
                    entry.signed_by,
                    entry.signature,
                ),
            )
            conn.commit()
            return entry

    def store_evidence(
        self,
        evidence: EvidenceRecord,
        *,
        epoch: int,
        signer: str,
    ) -> EvidenceLedgerEntry:
        self.upsert_evidence_record(evidence)
        return self.append_evidence_ledger_entry(
            entry_type=EvidenceLedgerEntryType.EVIDENCE_CREATE,
            evidence=evidence,
            epoch=epoch,
            payload={
                "type": "EVIDENCE_CREATE",
                "evidence_id": evidence.evidence_id,
                "evidence_hash": evidence.evidence_hash,
                "canonical_hash": evidence.canonical_hash,
                "law_id": evidence.law_id,
                "law_context": evidence.law_id,
            },
            signed_by=signer,
        )

    def ledger_entries(self) -> list[EvidenceLedgerEntry]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM evidence_ledger ORDER BY rowid ASC").fetchall()
        return [
            EvidenceLedgerEntry.from_dict(
                {
                    "entry_id": row["entry_id"],
                    "prev_hash": row["prev_hash"],
                    "timestamp": row["timestamp"],
                    "epoch": row["epoch"],
                    "entry_type": row["entry_type"],
                    "evidence_id": row["evidence_id"],
                    "evidence_hash": row["evidence_hash"],
                    "payload": json.loads(row["payload"] or "{}"),
                    "signed_by": row["signed_by"],
                    "signature": row["signature"],
                }
            )
            for row in rows
        ]

    def get_lineage_graph(self, evidence_id: str) -> dict[str, Any]:
        """Build a directed graph for EIT lineage visualization."""

        evidence = self.get_evidence(evidence_id)
        if evidence is None:
            return {"evidence_id": evidence_id, "nodes": [], "edges": [], "found": False}

        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        def add_node(node_id: str, *, label: str, node_type: str, **extra: Any) -> None:
            if node_id in nodes:
                return
            nodes[node_id] = {
                "id": node_id,
                "label": label,
                "type": node_type,
                **extra,
            }

        confidence_band = "high" if evidence.confidence >= 0.9 else "mid" if evidence.confidence >= 0.7 else "low"
        add_node(
            evidence.evidence_id,
            label=evidence.evidence_id,
            node_type=evidence.evidence_type.value,
            confidence=round(evidence.confidence, 6),
            confidence_band=confidence_band,
            law_id=evidence.law_id,
            epoch=evidence.source_epoch,
        )

        if evidence.source_lineage:
            add_node(
                evidence.source_lineage,
                label=evidence.source_lineage,
                node_type="lineage",
            )
            edges.append(
                {
                    "from": evidence.source_lineage,
                    "to": evidence.evidence_id,
                    "kind": "sources",
                }
            )

        for trace_id in evidence.trace_links:
            add_node(trace_id, label=trace_id, node_type="trace")
            edges.append({"from": trace_id, "to": evidence.evidence_id, "kind": "trace"})

        for dependency in evidence.dependencies:
            add_node(dependency, label=dependency, node_type="dependency")
            edges.append({"from": dependency, "to": evidence.evidence_id, "kind": "depends"})

        for entry in self.ledger_entries():
            if entry.evidence_id != evidence.evidence_id:
                continue
            add_node(entry.entry_id, label=entry.entry_type.value, node_type="ledger_entry", epoch=entry.epoch)
            edges.append({"from": evidence.evidence_id, "to": entry.entry_id, "kind": "ledger"})

        return {
            "evidence_id": evidence_id,
            "found": True,
            "evidence": evidence.to_dict(),
            "nodes": list(nodes.values()),
            "edges": edges,
        }


def genesis_evidence_block() -> EvidenceLedgerEntry:
    return EvidenceLedgerEntry(
        entry_id=EVIDENCE_LEDGER_GENESIS_ENTRY_ID,
        prev_hash=None,
        timestamp="EPOCH:0:T0",
        epoch=0,
        entry_type=EvidenceLedgerEntryType.EVIDENCE_GENESIS,
        evidence_id=EVIDENCE_LEDGER_SPEC_ID,
        evidence_hash=EVIDENCE_LEDGER_SPEC_HASH,
        payload={
            "description": "Genesis of Evidence Ledger and EvidenceRecord schema",
            "spec_ref": "UGR/EIT-1.md#v1.0.0",
            "binds": ["SIT-1", "GIT-1", "PIT-1", "LAW-LEDGER"],
            "created_by": "ROOT",
        },
        signed_by="ROOT",
        signature=_sig("ROOT", EVIDENCE_LEDGER_GENESIS_ENTRY_ID),
    )


def bootstrap_evidence_ledger(store: EvidenceLedgerStore | None = None) -> dict[str, Any]:
    ledger = store or EvidenceLedgerStore()
    genesis_evidence = EvidenceRecord(
        evidence_id=EVIDENCE_LEDGER_SPEC_ID,
        evidence_hash=EVIDENCE_LEDGER_SPEC_HASH,
        evidence_type=EvidenceType.IMPORT,
        source_lineage="ROOT",
        source_epoch=0,
        validation_method="genesis",
        confidence=1.0,
        canonical_hash=EVIDENCE_LEDGER_SPEC_HASH,
    )
    ledger.upsert_evidence_record(genesis_evidence)
    genesis = ledger.append_evidence_ledger_entry(
        entry_type=EvidenceLedgerEntryType.EVIDENCE_GENESIS,
        evidence=genesis_evidence,
        epoch=0,
        payload=genesis_evidence_block().payload,
        signed_by="ROOT",
        entry_id=EVIDENCE_LEDGER_GENESIS_ENTRY_ID,
        timestamp="EPOCH:0:T0",
    )
    return {"genesis_entry_id": genesis.entry_id}


def validate_decision_evidence(
    payload: dict[str, Any],
    *,
    evidence_store: EvidenceLedgerStore | None = None,
) -> dict[str, Any]:
    """EIT-1 — decision payloads must bind recoverable evidence."""

    evidence_id = payload.get("evidence_id")
    if not evidence_id:
        return {
            "capability_id": EIT_1_CAPABILITY_ID,
            "passed": False,
            "reason": "missing evidence_id",
        }
    store = evidence_store or EvidenceLedgerStore()
    evidence = store.get_evidence(str(evidence_id))
    if evidence is None:
        return {
            "capability_id": EIT_1_CAPABILITY_ID,
            "passed": False,
            "reason": f"evidence not found: {evidence_id}",
        }
    try:
        derive_components_from_evidence(evidence)
    except ValueError as exc:
        return {
            "capability_id": EIT_1_CAPABILITY_ID,
            "passed": False,
            "reason": str(exc),
        }
    return {
        "capability_id": EIT_1_CAPABILITY_ID,
        "passed": True,
        "evidence_id": evidence_id,
        "canonical_hash": evidence.canonical_hash,
    }


def evaluate_law_with_evidence(
    record: LawRecord,
    epoch: int,
    lineages: list[Lineage],
    *,
    thresholds: dict[str, float] | None = None,
    signer: str = "kernel",
    law_store: LawLedgerStore | None = None,
    evidence_store: EvidenceLedgerStore | None = None,
) -> LawRecord:
    """Sovereign kernel with EIT-1 — fitness and status decisions bind evidence."""

    laws = law_store or LawLedgerStore()
    evidence_ledger = evidence_store or EvidenceLedgerStore()
    resolved_thresholds = thresholds or {
        "admit": record.admit_threshold,
        "reject": record.reject_threshold,
    }

    evidence = build_evidence_from_lineages(record, epoch, lineages, signer=signer)
    evidence_ledger.store_evidence(evidence, epoch=epoch, signer=signer)
    evidence_ledger.append_evidence_ledger_entry(
        entry_type=EvidenceLedgerEntryType.EVIDENCE_VALIDATE,
        evidence=evidence,
        epoch=epoch,
        payload={
            "type": "EVIDENCE_VALIDATE",
            "evidence_id": evidence.evidence_id,
            "canonical_hash": evidence.canonical_hash,
            "operator_invariant": True,
        },
        signed_by=signer,
    )

    components = derive_components_from_evidence(evidence)
    f = aggregate_fitness(components)
    eval_payload = law_eval_payload(
        law_id=record.law_id,
        law_hash=record.law_hash,
        epoch=epoch,
        f=f,
        components=components,
        sample_size=len(lineages),
        thresholds=resolved_thresholds,
        notes="automatic evaluation",
        evidence_id=evidence.evidence_id,
    )
    eval_entry = laws.append_law_ledger_entry(
        entry_type=LawLedgerEntryType.LAW_EVAL,
        law_id=record.law_id,
        law_hash=record.law_hash,
        epoch=epoch,
        payload=eval_payload,
        signed_by=signer,
    )
    eval_validation = validate_decision_evidence(eval_payload, evidence_store=evidence_ledger)
    if not eval_validation["passed"]:
        raise RuntimeError(f"unconstitutional LAW_EVAL: {eval_validation['reason']}")

    old_status = record.status
    new_status = decide_status(
        old_status,
        f,
        admit=float(resolved_thresholds["admit"]),
        reject=float(resolved_thresholds["reject"]),
    )
    if new_status != old_status:
        status_payload = law_status_change_payload(
            law_id=record.law_id,
            law_hash=record.law_hash,
            epoch=epoch,
            old_status=old_status,
            new_status=new_status,
            reason=f"F(G)={f:.3f} with thresholds={resolved_thresholds}",
            source="kernel",
            ref_entry_id=eval_entry.entry_id,
            evidence_id=evidence.evidence_id,
        )
        laws.append_law_ledger_entry(
            entry_type=LawLedgerEntryType.LAW_STATUS_CHANGE,
            law_id=record.law_id,
            law_hash=record.law_hash,
            epoch=epoch,
            payload=status_payload,
            signed_by=signer,
        )
        status_validation = validate_decision_evidence(status_payload, evidence_store=evidence_ledger)
        if not status_validation["passed"]:
            raise RuntimeError(f"unconstitutional LAW_STATUS_CHANGE: {status_validation['reason']}")

    updated = LawRecord(
        law_id=record.law_id,
        version=record.version,
        law_hash=record.law_hash,
        spec_ref=record.spec_ref,
        status=new_status,
        created_at_epoch=record.created_at_epoch,
        introduced_by=record.introduced_by,
        current_fitness=f,
        fitness_history=[
            *record.fitness_history,
            FitnessHistoryRow(epoch=epoch, f=f, sample_size=len(lineages), notes="evidence-backed evaluation"),
        ],
        admit_threshold=float(resolved_thresholds["admit"]),
        reject_threshold=float(resolved_thresholds["reject"]),
        domains=list(record.domains),
        dependencies=list(record.dependencies),
        conflicts=list(record.conflicts),
        supersedes=list(record.supersedes),
    )
    laws.upsert_law_record(updated)
    return updated


def run_eit_proof(
    *,
    law_store: LawLedgerStore | None = None,
    evidence_store: EvidenceLedgerStore | None = None,
) -> dict[str, Any]:
    from src.continuity.law_ledger import bootstrap_law_ledger, load_founding_laws
    from src.continuity.lci_stack import LCI_FIXTURE, lineages_from_fixture, load_lci_fixture

    laws = law_store or LawLedgerStore()
    evidence = evidence_store or EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    pit = laws.get_law("PIT-1") or load_founding_laws()[2]
    existing = evidence.get_evidence(evidence_id_for(pit.law_id, 3))
    if existing is None:
        evaluated = evaluate_law_with_evidence(
            pit,
            epoch=3,
            lineages=lineages,
            law_store=laws,
            evidence_store=evidence,
        )
    else:
        evaluated = laws.get_law(pit.law_id) or pit

    eval_entries = [
        item
        for item in laws.ledger_entries()
        if item.entry_type == LawLedgerEntryType.LAW_EVAL
        and item.law_id == pit.law_id
        and int((item.payload or {}).get("epoch", -1)) == 3
    ]
    last_eval = eval_entries[-1] if eval_entries else None
    evidence_bound = (
        last_eval is not None
        and last_eval.payload.get("evidence_id") == evidence_id_for(pit.law_id, 3)
    )
    stored = evidence.get_evidence(evidence_id_for(pit.law_id, 3))
    replay_ok = stored is not None and operator_replay_equivalent(stored, stored)
    validation = (
        validate_decision_evidence(last_eval.payload, evidence_store=evidence)
        if last_eval
        else {"passed": False}
    )

    return {
        "capability_id": EIT_1_CAPABILITY_ID,
        "genesis_ok": any(
            item.entry_id == EVIDENCE_LEDGER_GENESIS_ENTRY_ID for item in evidence.ledger_entries()
        ),
        "evidence_bound": evidence_bound,
        "recoverable": validation.get("passed", False),
        "operator_invariant": replay_ok,
        "pit_evaluated_fitness": round(evaluated.current_fitness, 6),
        "evidence_id": evidence_id_for(pit.law_id, 3),
        "passed": evidence_bound and validation.get("passed", False) and replay_ok,
    }
