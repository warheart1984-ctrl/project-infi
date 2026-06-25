"""Authoritative Alpha governed loop orchestration (0001 → 1000 → 1001)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.runtime.schemas import CoreLoopRequest, CoreLoopResponse
from src.runtime.services.asset import create_asset
from src.runtime.services.audit import emit_audit_record
from src.runtime.services.evidence import attach_evidence
from src.runtime.services.identity import register_or_resolve_subject
from src.runtime.services.validation import submit_validation


def run_core_loop(db: Session, request: CoreLoopRequest) -> CoreLoopResponse:
    """
    Execute the six-step Alpha loop in order:
    identity → asset → evidence → validation → audit → response.
    """
    subject_id = register_or_resolve_subject(db, request)
    asset_id = create_asset(db, subject_id=subject_id, asset=request.asset)
    evidence_id = attach_evidence(db, asset_id=asset_id, evidence=request.evidence)
    validation_id, decision = submit_validation(
        db,
        asset_id=asset_id,
        evidence_id=evidence_id,
        evidence_input=request.evidence,
    )

    audit_id = emit_audit_record(
        db,
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
    db.commit()

    return CoreLoopResponse(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
        audit_id=audit_id,
    )
