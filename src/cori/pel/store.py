"""SQLite persistence for canonical PEL records."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from src.cori.store_paths import pel_store_path

PEL_SCHEMA = """
CREATE TABLE IF NOT EXISTS pel_records (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT,
  description TEXT,
  source_uri TEXT,
  hash TEXT NOT NULL,
  payload_summary TEXT,
  created_at TEXT,
  author TEXT,
  steward_role TEXT,
  links_json TEXT,
  evidence_strength TEXT,
  verified INTEGER DEFAULT 0,
  verified_by TEXT,
  verified_at TEXT,
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_pel_type ON pel_records(type);
CREATE INDEX IF NOT EXISTS idx_pel_author ON pel_records(author);
CREATE INDEX IF NOT EXISTS idx_pel_hash ON pel_records(hash);
"""

PEL_RECORD_TYPES = frozenset(
    {
        "artifact",
        "claim",
        "execution",
        "validation",
        "law_record",
        "panel",
        "correspondence",
        "core_loop_audit",
    }
)
EVIDENCE_STRENGTHS = frozenset({"primary", "secondary", "inferred"})


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_pel_id() -> str:
    return f"PEL-{uuid.uuid4().hex}"


def ensure_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or pel_store_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(PEL_SCHEMA)
    conn.commit()
    return conn


def find_by_hash(conn: sqlite3.Connection, content_hash: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM pel_records WHERE hash = ? LIMIT 1", (content_hash,)).fetchone()
    return dict(row) if row else None


def insert_pel_record(conn: sqlite3.Connection, record: dict[str, Any]) -> None:
    """Insert a PEL record. Keys must match the pel_records schema."""
    sql = """
    INSERT INTO pel_records (
      id, type, title, description, source_uri, hash, payload_summary,
      created_at, author, steward_role, links_json, evidence_strength,
      verified, verified_by, verified_at, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        record["id"],
        record["type"],
        record.get("title"),
        record.get("description"),
        record.get("source_uri"),
        record["hash"],
        json.dumps(record.get("payload_summary") or {}, sort_keys=True),
        record.get("created_at") or now_iso(),
        record.get("author"),
        record.get("steward_role"),
        json.dumps(record.get("links") or [], sort_keys=True),
        record.get("evidence_strength"),
        1 if record.get("verified") else 0,
        record.get("verified_by"),
        record.get("verified_at"),
        record.get("notes"),
    )
    conn.execute(sql, params)


def build_pel_record(
    *,
    type_: str,
    author: str,
    norm: dict[str, Any],
    steward_role: str | None = None,
    description: str | None = None,
    links: Iterable[dict[str, str]] | None = None,
    evidence_strength: str = "primary",
    created_at: str | None = None,
    notes: str | None = None,
    pel_id: str | None = None,
) -> dict[str, Any]:
    if type_ not in PEL_RECORD_TYPES:
        raise ValueError(f"unsupported PEL type: {type_}")
    if evidence_strength not in EVIDENCE_STRENGTHS:
        raise ValueError(f"unsupported evidence strength: {evidence_strength}")

    return {
        "id": pel_id or make_pel_id(),
        "type": type_,
        "title": norm["title"],
        "description": description,
        "source_uri": norm.get("source_uri"),
        "hash": norm["hash"],
        "payload_summary": norm.get("payload_summary") or {},
        "created_at": created_at or now_iso(),
        "author": author,
        "steward_role": steward_role,
        "links": list(links or []),
        "evidence_strength": evidence_strength,
        "verified": False,
        "verified_by": None,
        "verified_at": None,
        "notes": notes,
    }


def upsert_pel_record(
    conn: sqlite3.Connection,
    record: dict[str, Any],
    *,
    skip_duplicates: bool = True,
) -> tuple[dict[str, Any], bool]:
    """
    Insert a PEL record. When skip_duplicates is True, return existing row for the same hash.
    Returns (record, inserted).
    """
    if skip_duplicates:
        existing = find_by_hash(conn, record["hash"])
        if existing:
            return existing, False
    insert_pel_record(conn, record)
    return record, True
