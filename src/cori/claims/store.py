"""SQLite persistence for the canonical claim registry."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.cori.store_paths import claim_registry_path

_MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "claim_registry.sql"

CLAIM_KINDS = frozenset(
    {"stewardship", "ownership", "economic", "governance", "attribution", "other"}
)
GOVERNED_CLAIM_KINDS = frozenset(
    {"stewardship", "ownership", "economic", "governance", "attribution"}
)
CLAIM_STATUSES = frozenset({"draft", "active", "revoked", "superseded"})
CLAIM_TIERS = frozenset({"T1", "T2", "T3"})
LINK_RELATIONS = frozenset({"supports", "refutes", "context", "derived_from"})
LINK_STRENGTHS = frozenset({"primary", "secondary", "inferred"})
SUBJECT_TYPES = frozenset({"asset", "repo", "org", "person", "system", "other"})


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_claim_id() -> str:
    return f"CLAIM-{uuid.uuid4().hex}"


def _load_schema() -> str:
    return _MIGRATION.read_text(encoding="utf-8")


def ensure_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or claim_registry_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_load_schema())
    conn.commit()
    return conn


def insert_claim(
    conn: sqlite3.Connection,
    *,
    claim_id: str | None = None,
    kind: str,
    summary: str,
    created_by: str,
    description: str | None = None,
    subject_id: str | None = None,
    subject_type: str | None = None,
    created_at: str | None = None,
    status: str = "draft",
    tier: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    if kind not in CLAIM_KINDS:
        raise ValueError(f"unsupported claim kind: {kind}")
    if status not in CLAIM_STATUSES:
        raise ValueError(f"unsupported claim status: {status}")
    if tier is not None and tier not in CLAIM_TIERS:
        raise ValueError(f"unsupported claim tier: {tier}")
    if subject_type is not None and subject_type not in SUBJECT_TYPES:
        raise ValueError(f"unsupported subject_type: {subject_type}")

    record = {
        "id": claim_id or make_claim_id(),
        "kind": kind,
        "summary": summary,
        "description": description,
        "subject_id": subject_id,
        "subject_type": subject_type,
        "created_at": created_at or now_iso(),
        "created_by": created_by,
        "status": status,
        "tier": tier,
        "notes": notes,
    }
    conn.execute(
        """
        INSERT INTO claims (
          id, kind, summary, description, subject_id, subject_type,
          created_at, created_by, status, tier, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["id"],
            record["kind"],
            record["summary"],
            record["description"],
            record["subject_id"],
            record["subject_type"],
            record["created_at"],
            record["created_by"],
            record["status"],
            record["tier"],
            record["notes"],
        ),
    )
    return record


def insert_claim_evidence_link(
    conn: sqlite3.Connection,
    *,
    claim_id: str,
    pel_id: str,
    relation: str,
    strength: str,
    created_by: str,
    created_at: str | None = None,
) -> dict[str, Any]:
    if relation not in LINK_RELATIONS:
        raise ValueError(f"unsupported link relation: {relation}")
    if strength not in LINK_STRENGTHS:
        raise ValueError(f"unsupported link strength: {strength}")

    link = {
        "claim_id": claim_id,
        "pel_id": pel_id,
        "relation": relation,
        "strength": strength,
        "created_at": created_at or now_iso(),
        "created_by": created_by,
    }
    conn.execute(
        """
        INSERT INTO claim_evidence_links (
          claim_id, pel_id, relation, strength, created_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            link["claim_id"],
            link["pel_id"],
            link["relation"],
            link["strength"],
            link["created_at"],
            link["created_by"],
        ),
    )
    return link


def get_claim(conn: sqlite3.Connection, claim_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
    return dict(row) if row else None


def list_evidence_links_for_claim(conn: sqlite3.Connection, claim_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM claim_evidence_links WHERE claim_id = ? ORDER BY created_at",
        (claim_id,),
    ).fetchall()
    return [dict(row) for row in rows]
