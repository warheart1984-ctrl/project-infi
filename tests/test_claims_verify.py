"""Tests for claim registry store and verification."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.cori.claims.store import (
    ensure_db,
    insert_claim,
    insert_claim_evidence_link,
    make_claim_id,
)
from src.cori.claims.verify_store import list_claim_gaps, verify_claim_registry
from src.cori.pel.store import build_pel_record, ensure_db as ensure_pel_db, insert_pel_record
from src.cori.pel.normalize import normalize_text


@pytest.fixture()
def registry_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "claim_registry.sqlite3"
    pel_path = tmp_path / "pel.sqlite3"
    monkeypatch.setenv("CLAIM_REGISTRY_PATH", str(db_path))
    monkeypatch.setenv("PEL_STORE_PATH", str(pel_path))
    conn = ensure_db(db_path)
    pel_conn = ensure_pel_db(pel_path)
    yield conn, pel_conn, db_path, pel_path
    conn.close()
    pel_conn.close()


def _pel_record(pel_conn, pel_id: str = "PEL-doc-1") -> str:
    norm = normalize_text("evidence", {"title": "Primary doc"})
    record = build_pel_record(type_="artifact", author="jon", norm=norm, pel_id=pel_id)
    insert_pel_record(pel_conn, record)
    pel_conn.commit()
    return record["id"]


def test_empty_registry_passes(registry_db) -> None:
    conn, _pel, db_path, _ = registry_db
    conn.close()
    report = verify_claim_registry(db_path, create_if_missing=False)
    assert report["ok"] is True


def test_active_governed_claim_without_evidence_fails(registry_db) -> None:
    conn, _pel, db_path, _ = registry_db
    insert_claim(
        conn,
        claim_id="CLAIM-1",
        kind="stewardship",
        summary="Jon stewards repo X",
        created_by="jon",
        status="active",
    )
    conn.commit()
    conn.close()
    report = verify_claim_registry(db_path)
    assert report["ok"] is False
    assert any("CLAIM-1" in err for err in report["errors"])


def test_active_claim_with_primary_link_passes(registry_db) -> None:
    conn, pel_conn, db_path, _ = registry_db
    pel_id = _pel_record(pel_conn)
    claim = insert_claim(
        conn,
        claim_id="CLAIM-2",
        kind="ownership",
        summary="Org owns asset Y",
        created_by="jon",
        status="active",
    )
    insert_claim_evidence_link(
        conn,
        claim_id=claim["id"],
        pel_id=pel_id,
        relation="supports",
        strength="primary",
        created_by="jon",
    )
    conn.commit()
    conn.close()
    report = verify_claim_registry(db_path)
    assert report["ok"] is True


def test_t1_draft_without_evidence_fails(registry_db) -> None:
    conn, _pel, db_path, _ = registry_db
    insert_claim(
        conn,
        claim_id="CLAIM-t1",
        kind="other",
        summary="T1 policy claim",
        created_by="jon",
        status="draft",
        tier="T1",
    )
    conn.commit()
    conn.close()
    report = verify_claim_registry(db_path)
    assert report["ok"] is False
    assert any("T1" in err for err in report["errors"])


def test_list_claim_gaps(registry_db) -> None:
    conn, _pel, db_path, _ = registry_db
    insert_claim(
        conn,
        claim_id="CLAIM-gap",
        kind="governance",
        summary="Board approves budget",
        created_by="jon",
        status="active",
    )
    insert_claim(
        conn,
        claim_id="CLAIM-ok",
        kind="economic",
        summary="Revenue share defined",
        created_by="jon",
        status="active",
    )
    conn.commit()
    gaps = list_claim_gaps(conn)
    assert len(gaps) == 2
    assert {g["claim_id"] for g in gaps} == {"CLAIM-gap", "CLAIM-ok"}
    conn.close()


def test_make_claim_id_prefix() -> None:
    assert make_claim_id().startswith("CLAIM-")


def test_cli_json_output(tmp_path: Path) -> None:
    db_path = tmp_path / "claim_registry.sqlite3"
    conn = ensure_db(db_path)
    conn.close()

    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "claims_verify.py"),
            "--db",
            str(db_path),
            "--json",
            "--create-if-missing",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["ok"] is True
