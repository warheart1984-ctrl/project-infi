"""Read-only queries over the PEL SQLite store for dashboard APIs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.cori.pel.verify_store import (
    CLAIM_TYPE,
    PRIMARY_RELATION,
    PRIMARY_STRENGTH,
    load_primary_evidence_for_claim,
    open_db,
    parse_links,
)
from src.cori.store_paths import pel_store_path


def pel_db_path() -> Path:
    return pel_store_path()


def get_connection() -> sqlite3.Connection:
    path = pel_db_path()
    if not path.is_file():
        raise FileNotFoundError(f"PEL database not found at {path}")
    return open_db(path)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "type": row["type"],
        "title": row["title"],
        "description": row["description"],
        "source_uri": row["source_uri"],
        "hash": row["hash"],
        "payload_summary": json.loads(row["payload_summary"] or "{}"),
        "created_at": row["created_at"],
        "author": row["author"],
        "steward_role": row["steward_role"],
        "links": json.loads(row["links_json"] or "[]"),
        "evidence_strength": row["evidence_strength"],
        "verified": bool(row["verified"]),
        "verified_by": row["verified_by"],
        "verified_at": row["verified_at"],
        "notes": row["notes"],
    }


def list_pel_records(
    *,
    type_: str | None = None,
    author: str | None = None,
    evidence_strength: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        sql = "SELECT * FROM pel_records WHERE 1=1"
        params: list[Any] = []
        if type_:
            sql += " AND type = ?"
            params.append(type_)
        if author:
            sql += " AND author = ?"
            params.append(author)
        if evidence_strength:
            sql += " AND evidence_strength = ?"
            params.append(evidence_strength)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_pel_record(pel_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM pel_records WHERE id = ?", (pel_id,)).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def primary_evidence_for_claim(claim_id: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        claim = conn.execute(
            "SELECT id FROM pel_records WHERE id = ? AND type = ?",
            (claim_id, CLAIM_TYPE),
        ).fetchone()
        if not claim:
            return []
        rows = load_primary_evidence_for_claim(conn, claim_id)
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def claims_supported_by_evidence(pel_id: str) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM pel_records WHERE id = ?", (pel_id,)).fetchone()
        if not row:
            return None
        claim_ids = [
            link["target_id"]
            for link in parse_links(row)
            if link.get("relation") == PRIMARY_RELATION and link.get("target_id")
        ]
        if not claim_ids:
            return []
        placeholders = ",".join("?" for _ in claim_ids)
        rows = conn.execute(
            f"SELECT * FROM pel_records WHERE id IN ({placeholders}) AND type = ?",
            [*claim_ids, CLAIM_TYPE],
        ).fetchall()
        return [row_to_dict(r) for r in rows]
    finally:
        conn.close()


def list_claims_missing_primary_evidence() -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        claims = conn.execute("SELECT * FROM pel_records WHERE type = ?", (CLAIM_TYPE,)).fetchall()
        primaries = conn.execute(
            "SELECT * FROM pel_records WHERE evidence_strength = ?",
            (PRIMARY_STRENGTH,),
        ).fetchall()

        primary_map: dict[str, list[str]] = {}
        for row in primaries:
            for link in parse_links(row):
                if link.get("relation") == PRIMARY_RELATION:
                    target = link.get("target_id")
                    if target:
                        primary_map.setdefault(str(target), []).append(row["id"])

        gaps: list[dict[str, Any]] = []
        for claim in claims:
            claim_id = claim["id"]
            if claim_id not in primary_map:
                gaps.append(
                    {
                        "claim_id": claim_id,
                        "title": claim["title"],
                        "created_at": claim["created_at"],
                        "author": claim["author"],
                        "missing_primary_evidence": True,
                        "supporting_evidence_ids": [],
                    }
                )
            else:
                gaps.append(
                    {
                        "claim_id": claim_id,
                        "title": claim["title"],
                        "created_at": claim["created_at"],
                        "author": claim["author"],
                        "missing_primary_evidence": False,
                        "supporting_evidence_ids": primary_map[claim_id],
                    }
                )
        return [gap for gap in gaps if gap["missing_primary_evidence"]]
    finally:
        conn.close()
