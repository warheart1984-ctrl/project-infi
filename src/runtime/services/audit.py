"""Runtime audit service — immutable loop record with canonical payload hash."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from src.cori.pel.canonical import canonical_loop_payload, compute_loop_hash
from src.runtime.models import AuditRecord


def emit_audit_record(
    db: Session,
    *,
    subject_id: uuid.UUID,
    asset_id: uuid.UUID,
    evidence_id: uuid.UUID,
    validation_id: uuid.UUID,
    decision: str,
    loop_payload: dict[str, Any] | None = None,
) -> uuid.UUID:
    """POST runtime/v1/audit equivalent."""
    loop_hash = compute_loop_hash(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
    row = AuditRecord(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
        loop_hash=loop_hash,
    )
    db.add(row)
    db.flush()
    return row.id


def audit_payload(
    *,
    subject_id: uuid.UUID,
    asset_id: uuid.UUID,
    evidence_id: uuid.UUID,
    validation_id: uuid.UUID,
    decision: str,
    request_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical loop payload stored in PEL raw and used for primary_hash."""
    return canonical_loop_payload(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
