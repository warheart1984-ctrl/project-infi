"""Tests for PEL verification and report generation."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import pytest

from src.cori.pel.alpha_cycle import run_alpha_verification_cycle
from src.cori.pel.canonical import canonical_loop_payload, compute_hash
from src.cori.pel.generate_report import generate_json_report, generate_markdown_report, write_report_bundle
from src.cori.pel.ingest import default_t1_claim, pel_from_loop
from src.cori.pel.models import Claim, PELRecord
from src.cori.pel.pel_verify import verify_pel_record


def _sample_pel(*, loop_hash: str | None = None) -> PELRecord:
    subject_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    evidence_id = uuid.uuid4()
    validation_id = uuid.uuid4()
    raw = canonical_loop_payload(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision="approved",
    )
    primary = loop_hash or compute_hash(raw)
    return PELRecord(
        primary_hash=primary,
        actor_ref=str(subject_id),
        object_ref=str(asset_id),
        evidence_ref=str(evidence_id),
        validation_ref=str(validation_id),
        decision="approved",
        raw=raw,
        audit_id=str(uuid.uuid4()),
        observed_at=datetime(2026, 6, 22, 17, 58, 44, tzinfo=UTC),
    )


def test_verify_pel_record_matches_hash() -> None:
    pel = _sample_pel()
    claim = default_t1_claim()
    verif = verify_pel_record(pel, claim)
    assert verif.status == "verified"
    assert verif.details["message"] == "hash matches"
    assert verif.claim_id == claim.id
    assert verif.pel_record_id == pel.id


def test_verify_pel_record_detects_tamper() -> None:
    pel = _sample_pel(loop_hash="0" * 64)
    claim = default_t1_claim()
    verif = verify_pel_record(pel, claim)
    assert verif.status == "failed"
    assert verif.details["message"] == "hash mismatch"


def test_generate_markdown_report_contains_sections() -> None:
    pel = _sample_pel()
    claim = default_t1_claim()
    verif = verify_pel_record(pel, claim)
    md = generate_markdown_report(pel, claim, verif)
    assert "# CORI Alpha — First Verified Loop Report" in md
    assert claim.id in md
    assert pel.primary_hash in md
    assert "VERIFIED" in md
    assert "## 6. Conclusion" in md


def test_generate_json_report_structure() -> None:
    pel = _sample_pel()
    claim = Claim(summary="s", description="d")
    verif = verify_pel_record(pel, claim)
    report = generate_json_report(pel, claim, verif)
    assert report["interpretation"]["hash_match"] is True
    assert report["claim"]["id"] == claim.id
    assert report["pel_record"]["primary_hash"] == pel.primary_hash
    assert report["verification"]["status"] == "verified"
    assert report["verification"]["claim_id"] == claim.id


def test_write_report_bundle(tmp_path) -> None:
    pel = _sample_pel()
    claim = default_t1_claim()
    verif = verify_pel_record(pel, claim)
    paths = write_report_bundle(pel, claim, verif, tmp_path, stem="verified-loop")
    assert paths["markdown"].is_file()
    assert paths["json"].is_file()
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["verification_id"] == verif.id


def test_pel_from_loop_uses_audit_hash(runtime_db) -> None:
    from src.runtime import database as runtime_database
    from src.runtime.core_loop import run_core_loop
    from src.runtime.models import AuditRecord
    from src.runtime.schemas import CoreLoopRequest

    request = CoreLoopRequest.model_validate(
        {
            "email": "pel@example.com",
            "display_name": "PEL Steward",
            "asset": {"type": "document", "name": "PEL Asset"},
            "evidence": {"kind": "upload", "uri": "s3://bucket/pel", "hash": "cafebabe"},
        }
    )
    db = runtime_database.SessionLocal()
    try:
        response = run_core_loop(db, request)
        audit = db.get(AuditRecord, response.audit_id)
        assert audit is not None
        pel, claim, verif = run_alpha_verification_cycle(
            audit_id=response.audit_id,
            subject_id=response.subject_id,
            asset_id=response.asset_id,
            evidence_id=response.evidence_id,
            validation_id=response.validation_id,
            decision=response.decision,
            loop_hash=audit.loop_hash,
            request_body=request.model_dump(mode="json"),
        )
    finally:
        db.close()

    assert verif.status == "verified"
    assert claim.tier == "T1"
    assert claim.kind == "governance"
    assert pel.primary_hash == audit.loop_hash


def test_default_t1_claim_text() -> None:
    claim = default_t1_claim()
    assert "governed decision" in claim.summary
    assert claim.status == "active"


@pytest.fixture()
def runtime_db(tmp_path):
    from src.runtime.database import reset_runtime_engine

    db_path = tmp_path / "runtime_pel_test.db"
    url = f"sqlite:///{db_path.as_posix()}"
    reset_runtime_engine(url, create_tables=True)
    return url
