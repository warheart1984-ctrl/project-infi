"""Tests for PEL ingest normalization and SQLite writes."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.cori.pel.normalize import normalize_file, normalize_json_object
from src.cori.pel.pel_verify import canonical_payload_hash
from src.cori.pel.store import build_pel_record, ensure_db, find_by_hash, upsert_pel_record


@pytest.fixture()
def pel_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "pel.sqlite3"
    monkeypatch.setenv("PEL_STORE_PATH", str(db_path))
    conn = ensure_db(db_path)
    yield conn
    conn.close()


def test_normalize_file_hash_stable(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_text("# Charter\n", encoding="utf-8")
    first = normalize_file(path)
    second = normalize_file(path)
    assert first["hash"] == second["hash"]
    assert first["payload_summary"]["size"] == len(path.read_bytes())


def test_insert_and_find_by_hash(pel_db) -> None:
    norm = normalize_json_object({"event_type": "law_eval", "id": "evt-1", "payload": {"x": 1}})
    record = build_pel_record(type_="execution", author="system", norm=norm)
    stored, inserted = upsert_pel_record(pel_db, record)
    pel_db.commit()
    assert inserted is True
    found = find_by_hash(pel_db, record["hash"])
    assert found is not None
    assert found["id"] == stored["id"]


def test_skip_duplicate_hash(pel_db) -> None:
    norm = normalize_json_object({"id": "dup", "event_type": "urg_mission"})
    record = build_pel_record(type_="execution", author="system", norm=norm)
    upsert_pel_record(pel_db, record)
    pel_db.commit()
    _, inserted = upsert_pel_record(pel_db, build_pel_record(type_="execution", author="system", norm=norm))
    assert inserted is False


def test_json_object_uses_canonical_runtime_hash() -> None:
    row = {"decision": "approved", "subject_id": "abc", "validation_id": "def"}
    norm = normalize_json_object(row)
    assert norm["hash"] == canonical_payload_hash(row)


def test_cli_ingest_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "pel.sqlite3"
    doc = tmp_path / "charter.md"
    doc.write_text("CORI Alpha charter", encoding="utf-8")
    repo = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo)
    env["PEL_STORE_PATH"] = str(db_path)
    proc = subprocess.run(
        [
            sys.executable,
            str(repo / "scripts" / "pel_ingest.py"),
            "--file",
            str(doc),
            "--type",
            "artifact",
            "--author",
            "jon",
        ],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    body = json.loads(proc.stdout)
    assert body["hash"]
    assert body["_inserted"] is True
    conn = ensure_db(db_path)
    try:
        assert find_by_hash(conn, body["hash"]) is not None
    finally:
        conn.close()
