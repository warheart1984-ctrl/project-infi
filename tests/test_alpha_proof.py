"""Tests for the alpha_proof governance harness."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.alpha_proof import core_loop_payload, run_alpha_proof


@pytest.fixture()
def runtime_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runtime_db = tmp_path / "alpha_proof_runtime.db"
    evidence_db = tmp_path / "alpha_evidence.sqlite3"
    monkeypatch.setenv("RUNTIME_DATABASE_URL", f"sqlite:///{runtime_db.as_posix()}")
    monkeypatch.setenv("ALPHA_EVIDENCE_PATH", str(evidence_db))

    from src.runtime import api as runtime_api
    from src.runtime.database import reset_runtime_engine

    reset_runtime_engine(f"sqlite:///{runtime_db.as_posix()}", create_tables=True)
    runtime_api._runtime_db_ready = False

    import app.main as app_main

    with TestClient(app_main.app) as client:
        yield client


def test_core_loop_payload_matches_schema() -> None:
    payload = core_loop_payload()
    assert "uri" in payload["evidence"]
    assert "hash" in payload["evidence"]


def test_run_alpha_proof_in_process(runtime_client: TestClient) -> None:
    audit_id, pel, claim, verification = run_alpha_proof(client=runtime_client, persist=True)
    assert audit_id
    assert pel.primary_hash
    assert claim.tier == "T1"
    assert verification.status == "verified"
    assert verification.claim_id == claim.id
    assert verification.pel_record_id == pel.id
