"""Tests for PEL store verification (pel_verify.py rules)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.cori.pel.store import build_pel_record, ensure_db, insert_pel_record, upsert_pel_record
from src.cori.pel.normalize import normalize_json_object, normalize_text
from src.cori.pel.verify_store import verify_pel_store


@pytest.fixture()
def pel_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "pel.sqlite3"
    monkeypatch.setenv("PEL_STORE_PATH", str(db_path))
    conn = ensure_db(db_path)
    yield conn, db_path
    conn.close()


def _insert(conn, *, type_: str, author: str = "jon", links=None, strength: str = "primary", pel_id: str | None = None):
    norm = normalize_text(f"{type_}-{pel_id or 'x'}", {"title": type_})
    record = build_pel_record(
        type_=type_,
        author=author,
        norm=norm,
        links=links or [],
        evidence_strength=strength,
        pel_id=pel_id,
    )
    insert_pel_record(conn, record)
    conn.commit()
    return record


def test_verify_passes_on_valid_artifact(pel_db) -> None:
    conn, db_path = pel_db
    _insert(conn, type_="artifact")
    report = verify_pel_store(db_path)
    assert report["ok"] is True
    assert report["error_count"] == 0


def test_verify_fails_on_missing_hash(pel_db) -> None:
    conn, db_path = pel_db
    conn.execute(
        """
        INSERT INTO pel_records (id, type, hash, created_at, author, links_json, evidence_strength, verified)
        VALUES ('PEL-bad', 'artifact', '', '2026-01-01T00:00:00Z', 'jon', '[]', 'primary', 0)
        """
    )
    conn.commit()
    report = verify_pel_store(db_path)
    assert report["ok"] is False
    assert any("missing hash" in err for err in report["errors"])


def test_claim_without_primary_evidence_fails(pel_db) -> None:
    conn, db_path = pel_db
    claim = _insert(conn, type_="claim", pel_id="PEL-claim-1")
    report = verify_pel_store(db_path)
    assert report["ok"] is False
    assert any(claim["id"] in err for err in report["errors"])


def test_claim_with_primary_evidence_passes(pel_db) -> None:
    conn, db_path = pel_db
    claim = _insert(conn, type_="claim", pel_id="PEL-claim-2")
    _insert(
        conn,
        type_="artifact",
        links=[{"relation": "supports", "target_id": claim["id"]}],
        strength="primary",
    )
    report = verify_pel_store(db_path)
    assert report["ok"] is True


def test_invalid_links_json_fails(pel_db) -> None:
    conn, db_path = pel_db
    conn.execute(
        """
        INSERT INTO pel_records (id, type, hash, created_at, author, links_json, evidence_strength, verified)
        VALUES ('PEL-links', 'artifact', 'abc', '2026-01-01T00:00:00Z', 'jon', 'not-json', 'primary', 0)
        """
    )
    conn.commit()
    report = verify_pel_store(db_path)
    assert report["ok"] is False
    assert any("invalid links_json" in err for err in report["errors"])


def test_cli_json_output(tmp_path: Path) -> None:
    db_path = tmp_path / "pel.sqlite3"
    conn = ensure_db(db_path)
    norm = normalize_json_object({"id": "evt-1", "event_type": "law_eval"})
    record = build_pel_record(type_="execution", author="system", norm=norm)
    upsert_pel_record(conn, record)
    conn.commit()
    conn.close()

    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    proc = subprocess.run(
        [sys.executable, str(repo / "scripts" / "pel_verify.py"), "--db", str(db_path), "--json"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["ok"] is True
