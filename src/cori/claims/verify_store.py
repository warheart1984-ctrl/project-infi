"""Automated verification checks over the claim registry."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.cori.claims.store import (
    GOVERNED_CLAIM_KINDS,
    LINK_RELATIONS,
    LINK_STRENGTHS,
    ensure_db,
)
from src.cori.pel.verify_store import open_db as open_pel_db
from src.cori.store_paths import claim_registry_path, pel_store_path

PRIMARY_RELATION = "supports"
PRIMARY_STRENGTH = "primary"
ACTIVE_STATUS = "active"


def open_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or claim_registry_path()
    if not db_path.is_file():
        raise FileNotFoundError(f"Claim registry not found at {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _has_primary_support(conn: sqlite3.Connection, claim_id: str) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM claim_evidence_links
        WHERE claim_id = ? AND relation = ? AND strength = ?
        LIMIT 1
        """,
        (claim_id, PRIMARY_RELATION, PRIMARY_STRENGTH),
    ).fetchone()
    return row is not None


def check_active_governed_claims_primary_evidence(conn: sqlite3.Connection) -> list[str]:
    """
    Invariant: active governed-kind claims must have primary supporting evidence.
    """
    errors: list[str] = []
    placeholders = ",".join("?" for _ in GOVERNED_CLAIM_KINDS)
    rows = conn.execute(
        f"""
        SELECT id, kind, summary FROM claims
        WHERE status = ? AND kind IN ({placeholders})
        """,
        (ACTIVE_STATUS, *sorted(GOVERNED_CLAIM_KINDS)),
    ).fetchall()
    for row in rows:
        if not _has_primary_support(conn, row["id"]):
            errors.append(
                f"[CLAIM_PRIMARY] Active {row['kind']} claim {row['id']} "
                f"({row['summary']!r}) has no primary supporting evidence link"
            )
    return errors


def check_t1_claims_primary_evidence(conn: sqlite3.Connection) -> list[str]:
    """Invariant: T1-tier claims must have primary supporting evidence."""
    errors: list[str] = []
    rows = conn.execute(
        """
        SELECT id, kind, summary, status FROM claims
        WHERE tier = 'T1' AND status NOT IN ('revoked', 'superseded')
        """
    ).fetchall()
    for row in rows:
        if not _has_primary_support(conn, row["id"]):
            errors.append(
                f"[CLAIM_T1_PRIMARY] T1 claim {row['id']} ({row['summary']!r}) "
                f"has no primary supporting evidence link"
            )
    return errors


def check_link_sanity(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    rows = conn.execute("SELECT id, claim_id, pel_id, relation, strength FROM claim_evidence_links").fetchall()
    claim_ids = {row["id"] for row in conn.execute("SELECT id FROM claims").fetchall()}
    for row in rows:
        if row["claim_id"] not in claim_ids:
            errors.append(f"[LINKS] link {row['id']} references missing claim {row['claim_id']}")
        if row["relation"] not in LINK_RELATIONS:
            errors.append(f"[LINKS] link {row['id']} has unknown relation {row['relation']!r}")
        if row["strength"] not in LINK_STRENGTHS:
            errors.append(f"[LINKS] link {row['id']} has unknown strength {row['strength']!r}")
        if not row["pel_id"]:
            errors.append(f"[LINKS] link {row['id']} missing pel_id")
    return errors


def check_pel_references(conn: sqlite3.Connection, pel_conn: sqlite3.Connection | None) -> list[str]:
    """Warn-level cross-store check when PEL DB is available."""
    warnings: list[str] = []
    if pel_conn is None:
        return warnings
    pel_ids = {row["id"] for row in pel_conn.execute("SELECT id FROM pel_records").fetchall()}
    rows = conn.execute("SELECT id, pel_id FROM claim_evidence_links").fetchall()
    for row in rows:
        if row["pel_id"] not in pel_ids:
            warnings.append(
                f"[PEL_REF] claim_evidence_links {row['id']} references missing PEL record {row['pel_id']}"
            )
    return warnings


def list_claim_gaps(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Active governed claims missing primary supporting evidence."""
    placeholders = ",".join("?" for _ in GOVERNED_CLAIM_KINDS)
    rows = conn.execute(
        f"""
        SELECT id, kind, summary, created_at, created_by, status, tier
        FROM claims
        WHERE status = ? AND kind IN ({placeholders})
        """,
        (ACTIVE_STATUS, *sorted(GOVERNED_CLAIM_KINDS)),
    ).fetchall()
    gaps: list[dict[str, Any]] = []
    for row in rows:
        if not _has_primary_support(conn, row["id"]):
            gaps.append(
                {
                    "claim_id": row["id"],
                    "kind": row["kind"],
                    "summary": row["summary"],
                    "created_at": row["created_at"],
                    "created_by": row["created_by"],
                    "status": row["status"],
                    "tier": row["tier"],
                    "missing_primary_evidence": True,
                }
            )
    return gaps


def run_checks(
    conn: sqlite3.Connection,
    *,
    pel_conn: sqlite3.Connection | None = None,
    fail_on_warn: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_link_sanity(conn))
    errors.extend(check_active_governed_claims_primary_evidence(conn))
    errors.extend(check_t1_claims_primary_evidence(conn))
    warnings.extend(check_pel_references(conn, pel_conn))

    if fail_on_warn:
        errors.extend(warnings)
        warnings = []

    ok = len(errors) == 0
    return {
        "ok": ok,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def verify_claim_registry(
    db_path: Path | None = None,
    *,
    pel_db_path: Path | None = None,
    fail_on_warn: bool = False,
    create_if_missing: bool = False,
) -> dict[str, Any]:
    path = db_path or claim_registry_path()
    if not path.is_file():
        if create_if_missing:
            conn = ensure_db(path)
            conn.close()
        else:
            raise FileNotFoundError(f"Claim registry not found at {path}")

    pel_conn: sqlite3.Connection | None = None
    pel_path = pel_db_path or pel_store_path()
    if pel_path.is_file():
        pel_conn = open_pel_db(pel_path)

    conn = open_db(path)
    try:
        report = run_checks(conn, pel_conn=pel_conn, fail_on_warn=fail_on_warn)
        report["db_path"] = str(path)
        if pel_path.is_file():
            report["pel_db_path"] = str(pel_path)
        return report
    finally:
        conn.close()
        if pel_conn is not None:
            pel_conn.close()
