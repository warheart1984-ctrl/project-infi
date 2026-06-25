"""Tests for HTTP mesh runtime orchestrator."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from services.runtime.app import config as runtime_config
from services.runtime.app.api import audit_router, router as runtime_router
from src.cori.pel.canonical import compute_loop_hash
from services.runtime.app.orchestrator import CoreLoopRequest, run_core_loop
from services.runtime.mesh_handlers import mesh_router
from src.runtime import database as runtime_database
from src.runtime.database import reset_runtime_engine
from src.runtime.models import AuditRecord, Subject


def _combined_mesh_app() -> FastAPI:
    app = FastAPI()
    app.include_router(mesh_router)
    app.include_router(runtime_router)
    app.include_router(audit_router)
    return app


def test_compute_loop_hash_is_deterministic() -> None:
    subject_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    asset_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    evidence_id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    validation_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
    first = compute_loop_hash(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision="approved",
    )
    second = compute_loop_hash(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision="approved",
    )
    assert first == second
    assert len(first) == 64


@pytest.fixture()
def runtime_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "runtime_mesh.db"
    url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("RUNTIME_DATABASE_URL", url)
    reset_runtime_engine(url, create_tables=True)

    base = "http://testserver/v1"
    monkeypatch.setattr(runtime_config, "IDENTITY_URL", base)
    monkeypatch.setattr(runtime_config, "ASSET_URL", base)
    monkeypatch.setattr(runtime_config, "EVIDENCE_URL", base)
    monkeypatch.setattr(runtime_config, "VALIDATION_URL", base)
    monkeypatch.setattr(runtime_config, "AUDIT_URL", base)
    yield url


def test_mesh_orchestrator_end_to_end(runtime_db: str) -> None:
    async def _run() -> dict:
        transport = ASGITransport(app=_combined_mesh_app())
        payload = CoreLoopRequest(
            email="mesh@example.com",
            display_name="Mesh Steward",
            asset={"type": "document", "name": "Mesh Asset", "metadata": {"tier": "T1"}},
            evidence={"kind": "upload", "uri": "s3://bucket/object", "hash": "deadbeef"},
        )
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await run_core_loop(payload, client=client)

    result = asyncio.run(_run())

    assert result["decision"] == "approved"

    db = runtime_database.SessionLocal()
    try:
        audit = db.get(AuditRecord, result["audit_id"])
        subject = db.get(Subject, result["subject_id"])
        assert audit is not None
        assert subject is not None
        assert subject.email == "mesh@example.com"
        assert audit.loop_hash == compute_loop_hash(
            subject_id=result["subject_id"],
            asset_id=result["asset_id"],
            evidence_id=result["evidence_id"],
            validation_id=result["validation_id"],
            decision=result["decision"],
        )
    finally:
        db.close()
