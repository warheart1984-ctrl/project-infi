"""End-to-end Alpha evidence cycle integration tests."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.cori.pel.bootstrap_claims import create_alpha_t1_claim
from src.cori.pel.pel_register import register_pel_record
from src.cori.pel.pel_verify import verify_pel_record
from src.cori.pel.storage import ClaimStorage, PelStorage, VerificationStorage


@pytest.fixture()
def alpha_stores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "alpha_evidence.sqlite3"
    runtime_db = tmp_path / "runtime_e2e.db"
    monkeypatch.setenv("ALPHA_EVIDENCE_PATH", str(db_path))
    monkeypatch.setenv("RUNTIME_DATABASE_URL", f"sqlite:///{runtime_db.as_posix()}")

    from src.runtime import api as runtime_api
    from src.runtime.database import reset_runtime_engine

    reset_runtime_engine(f"sqlite:///{runtime_db.as_posix()}", create_tables=True)
    runtime_api._runtime_db_ready = False

    yield {
        "pel": PelStorage(db_path),
        "claim": ClaimStorage(db_path),
        "verification": VerificationStorage(db_path),
    }


def test_end_to_end_evidence_cycle(alpha_stores) -> None:
    import app.main as app_main

    client = TestClient(app_main.app)
    payload = {
        "email": "user@example.org",
        "display_name": "Test User",
        "asset": {
            "type": "document",
            "name": "Test Asset",
            "metadata": {"category": "example"},
        },
        "evidence": {
            "kind": "upload",
            "uri": "s3://bucket/object",
            "hash": "deadbeef",
        },
    }

    response = client.post("/v1/runtime/core-loop", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    audit_id = body["audit_id"]

    pel_record = register_pel_record(audit_id, alpha_stores["pel"], client=client)
    assert pel_record.primary_hash
    assert pel_record.audit_id == audit_id

    claim = create_alpha_t1_claim()
    alpha_stores["claim"].save_claim(claim)

    verification = verify_pel_record(pel_record, claim)
    alpha_stores["verification"].save_verification(verification)

    assert verification.status == "verified"
    assert verification.claim_id == claim.id
    assert verification.pel_record_id == pel_record.id

    loaded_pel = alpha_stores["pel"].get_by_id(pel_record.id)
    loaded_claim = alpha_stores["claim"].get_by_id(claim.id)
    loaded_verif = alpha_stores["verification"].get_by_id(verification.id)
    assert loaded_pel.id == pel_record.id
    assert loaded_claim.tier == "T1"
    assert loaded_verif.status == "verified"


def test_dashboard_evidence_cycles_endpoint(alpha_stores) -> None:
    from src.dashboard.app import app as dashboard_app

    pel = alpha_stores["pel"]
    claim_store = alpha_stores["claim"]
    verif_store = alpha_stores["verification"]

    from src.cori.pel.models import PELRecord, VerificationRecord
    from datetime import UTC, datetime

    pel_record = PELRecord(
        id=f"PEL-{uuid.uuid4().hex}",
        primary_hash="a" * 64,
        actor_ref=str(uuid.uuid4()),
        object_ref=str(uuid.uuid4()),
        evidence_ref=str(uuid.uuid4()),
        validation_ref=str(uuid.uuid4()),
        decision="approved",
        raw={
            "subject_id": "s",
            "asset_id": "a",
            "evidence_id": "e",
            "validation_id": "v",
            "decision": "approved",
        },
        observed_at=datetime.now(UTC),
    )
    pel.save_pel_record(pel_record)
    claim = create_alpha_t1_claim()
    claim_store.save_claim(claim)
    verification = VerificationRecord(
        claim_id=claim.id,
        pel_record_id=pel_record.id,
        status="verified",
        details={"message": "hash matches"},
        verified_at=datetime.now(UTC),
    )
    verif_store.save_verification(verification)

    client = TestClient(dashboard_app)
    response = client.get("/dashboard/evidence-cycles")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["pel"]["id"] == pel_record.id
    assert body[0]["claim"]["tier"] == "T1"
    assert body[0]["verification"]["status"] == "verified"
