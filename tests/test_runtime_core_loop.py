"""Tests for POST /v1/runtime/core-loop — Alpha governed loop contract."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.runtime import database as runtime_database
from src.runtime.core_loop import run_core_loop
from src.runtime.database import reset_runtime_engine
from src.runtime.models import Asset, AuditRecord, Evidence, Subject, ValidationRecord
from src.runtime.schemas import CoreLoopRequest


@pytest.fixture()
def runtime_db(tmp_path: Path):
    db_path = tmp_path / "runtime_core_test.db"
    url = f"sqlite:///{db_path.as_posix()}"
    reset_runtime_engine(url, create_tables=True)
    yield url


def _db():
    return runtime_database.SessionLocal()


def _sample_request(**overrides) -> CoreLoopRequest:
    body = {
        "email": "steward@example.com",
        "display_name": "Test Steward",
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
    body.update(overrides)
    return CoreLoopRequest.model_validate(body)


def test_core_loop_sequence_persists_five_entities(runtime_db: Path) -> None:
    request = _sample_request()
    db = _db()
    try:
        response = run_core_loop(db, request)
    finally:
        db.close()

    assert response.decision == "approved"
    assert isinstance(response.subject_id, uuid.UUID)
    assert isinstance(response.audit_id, uuid.UUID)

    db = _db()
    try:
        subject = db.get(Subject, response.subject_id)
        asset = db.get(Asset, response.asset_id)
        evidence = db.get(Evidence, response.evidence_id)
        validation = db.get(ValidationRecord, response.validation_id)
        audit = db.get(AuditRecord, response.audit_id)

        assert subject is not None
        assert subject.email == "steward@example.com"
        assert asset is not None
        assert asset.subject_id == response.subject_id
        assert evidence is not None
        assert evidence.asset_id == response.asset_id
        assert validation is not None
        assert validation.evidence_id == response.evidence_id
        assert audit is not None
        assert audit.loop_hash
        assert audit.validation_id == response.validation_id
    finally:
        db.close()


def test_identity_register_is_idempotent(runtime_db: Path) -> None:
    db = _db()
    try:
        first = run_core_loop(db, _sample_request())
        second = run_core_loop(
            db,
            _sample_request(
                asset={"type": "document", "name": "Second Asset"},
                evidence={"kind": "upload", "uri": "s3://bucket/other", "hash": "cafebabe"},
            ),
        )
    finally:
        db.close()

    assert first.subject_id == second.subject_id
    db = _db()
    try:
        count = len(db.execute(select(Subject)).scalars().all())
        assert count == 1
        assets = db.execute(select(Asset).where(Asset.subject_id == first.subject_id)).scalars().all()
        assert len(assets) == 2
    finally:
        db.close()


def test_validation_pending_for_unknown_uri_scheme(runtime_db: Path) -> None:
    db = _db()
    try:
        response = run_core_loop(
            db,
            _sample_request(evidence={"kind": "upload", "uri": "local://object", "hash": "deadbeef"}),
        )
    finally:
        db.close()
    assert response.decision == "pending"


def test_core_loop_http_endpoint(runtime_db: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNTIME_DATABASE_URL", runtime_db)
    runtime_database.reset_runtime_engine(runtime_db, create_tables=True)
    import src.runtime.api as runtime_api

    runtime_api._runtime_db_ready = False

    import app.main as app_main

    client = TestClient(app_main.app)
    response = client.post(
        "/v1/runtime/core-loop",
        json={
            "email": "http@example.com",
            "display_name": "HTTP Steward",
            "asset": {"type": "document", "name": "HTTP Asset", "metadata": {}},
            "evidence": {"kind": "upload", "uri": "https://example.com/doc", "hash": "abc123"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"] == "approved"
    assert body["subject_id"]
    assert body["audit_id"]
