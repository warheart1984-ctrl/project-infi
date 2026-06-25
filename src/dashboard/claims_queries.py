"""Read-only queries over the claim registry for dashboard APIs."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.cori.claims.store import ensure_db
from src.cori.claims.verify_store import list_claim_gaps, open_db
from src.cori.store_paths import claim_registry_path


def get_connection() -> sqlite3.Connection:
    path = claim_registry_path()
    if not path.is_file():
        raise FileNotFoundError(f"Claim registry not found at {path}")
    return open_db(path)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_claims(
    *,
    kind: str | None = None,
    status: str | None = None,
    subject_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        sql = "SELECT * FROM claims WHERE 1=1"
        params: list[Any] = []
        if kind:
            sql += " AND kind = ?"
            params.append(kind)
        if status:
            sql += " AND status = ?"
            params.append(status)
        if subject_id:
            sql += " AND subject_id = ?"
            params.append(subject_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_claim(claim_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def evidence_links_for_claim(claim_id: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM claim_evidence_links WHERE claim_id = ? ORDER BY created_at",
            (claim_id,),
        ).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def list_governed_claim_gaps() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        return list_claim_gaps(conn)
    finally:
        conn.close()


def ensure_registry_exists() -> None:
    """Create an empty registry when missing (read APIs return empty lists)."""
    ensure_db(claim_registry_path())
