"""Automated verification checks over the SQLite PEL store."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.cori.pel.store import ensure_db
from src.cori.store_paths import pel_store_path

CLAIM_TYPE = "claim"
PRIMARY_RELATION = "supports"
PRIMARY_STRENGTH = "primary"
KNOWN_RELATIONS = frozenset({"supports", "derived_from", "references", "contradicts", "supersedes"})


def open_db(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or pel_store_path()
    if not db_path.is_file():
        raise FileNotFoundError(f"PEL DB not found at {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def parse_links(row: sqlite3.Row) -> list[dict[str, Any]]:
    raw = row["links_json"]
    if not raw:
        return []
    try:
        links = json.loads(raw)
        if isinstance(links, list):
            return [link for link in links if isinstance(link, dict)]
    except json.JSONDecodeError:
        return []
    return []


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        normalized = ts[:-1] + "+00:00" if ts.endswith("Z") else ts
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def check_basic_fields(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    rows = conn.execute("SELECT id, type, hash, created_at, author FROM pel_records").fetchall()
    for row in rows:
        if not row["hash"]:
            errors.append(f"[BASIC] {row['id']} missing hash")
        if not row["type"]:
            errors.append(f"[BASIC] {row['id']} missing type")
        if not row["created_at"]:
            errors.append(f"[BASIC] {row['id']} missing created_at")
        if not row["author"]:
            errors.append(f"[BASIC] {row['id']} missing author")
    return errors


def check_links_sanity(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    rows = conn.execute("SELECT id, links_json FROM pel_records").fetchall()
    for row in rows:
        raw = row["links_json"]
        if not raw:
            continue
        try:
            links = json.loads(raw)
        except json.JSONDecodeError:
            errors.append(f"[LINKS] {row['id']} has invalid links_json")
            continue
        if not isinstance(links, list):
            errors.append(f"[LINKS] {row['id']} links_json is not a list")
            continue
        for link in links:
            if not isinstance(link, dict):
                errors.append(f"[LINKS] {row['id']} has non-dict link entry")
                continue
            relation = link.get("relation")
            target = link.get("target_id")
            if not relation or not target:
                errors.append(f"[LINKS] {row['id']} link missing relation or target_id")
                continue
            if relation not in KNOWN_RELATIONS:
                errors.append(f"[LINKS] {row['id']} has unknown relation {relation!r}")
    return errors


def check_timestamp_sanity(conn: sqlite3.Connection) -> list[str]:
    errors: list[str] = []
    rows = conn.execute("SELECT id, created_at FROM pel_records").fetchall()
    now = datetime.now(UTC)
    for row in rows:
        ts = parse_iso(row["created_at"])
        if ts is None:
            errors.append(f"[TIME] {row['id']} invalid timestamp {row['created_at']}")
            continue
        if ts > now and (ts - now).total_seconds() > 86400:
            errors.append(f"[TIME] {row['id']} timestamp far in future {row['created_at']}")
    return errors


def load_claims(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM pel_records WHERE type = ?", (CLAIM_TYPE,)).fetchall()


def load_primary_evidence_for_claim(conn: sqlite3.Connection, claim_id: str) -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT * FROM pel_records WHERE evidence_strength = ?",
        (PRIMARY_STRENGTH,),
    ).fetchall()
    matches: list[sqlite3.Row] = []
    for row in rows:
        for link in parse_links(row):
            if link.get("relation") == PRIMARY_RELATION and link.get("target_id") == claim_id:
                matches.append(row)
                break
    return matches


def load_primary_evidence(conn: sqlite3.Connection, claim_id: str) -> list[sqlite3.Row]:
    """Primary evidence rows that support a claim (alias for skeleton API)."""
    return load_primary_evidence_for_claim(conn, claim_id)


def check_claim_primary_evidence(conn: sqlite3.Connection) -> list[str]:
    """Claim invariant only — returns errors (warnings printed by run_checks)."""
    errors, _warnings = check_no_claim_without_primary_evidence(conn)
    return errors


def check_no_claim_without_primary_evidence(conn: sqlite3.Connection) -> tuple[list[str], list[str]]:
    """
    Invariant: every claim must have at least one primary evidence record linked via supports.
    Returns (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []
    claims = load_claims(conn)
    if not claims:
        warnings.append("[WARN] No claims found in PEL.")
        return errors, warnings

    for claim in claims:
        claim_id = claim["id"]
        primary = load_primary_evidence_for_claim(conn, claim_id)
        if not primary:
            errors.append(f"[CLAIM_PRIMARY] Claim {claim_id} has no primary evidence record")
    return errors, warnings


def run_checks(conn: sqlite3.Connection, *, fail_on_warn: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_basic_fields(conn))
    errors.extend(check_links_sanity(conn))
    errors.extend(check_timestamp_sanity(conn))

    claim_errors, claim_warnings = check_no_claim_without_primary_evidence(conn)
    errors.extend(claim_errors)
    warnings.extend(claim_warnings)

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


def verify_pel_store(
    db_path: Path | None = None,
    *,
    fail_on_warn: bool = False,
    create_if_missing: bool = False,
) -> dict[str, Any]:
    path = db_path or pel_store_path()
    if not path.is_file():
        if create_if_missing:
            conn = ensure_db(path)
            conn.close()
        else:
            raise FileNotFoundError(f"PEL DB not found at {path}")

    conn = open_db(path)
    try:
        report = run_checks(conn, fail_on_warn=fail_on_warn)
        report["db_path"] = str(path)
        return report
    finally:
        conn.close()
