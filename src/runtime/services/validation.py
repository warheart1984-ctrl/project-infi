"""Validation service — Alpha immediate decision on evidence."""

from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy.orm import Session

from src.runtime.models import Evidence, ValidationRecord
from src.runtime.schemas import EvidenceInput

Decision = Literal["approved", "rejected", "pending"]
ALPHA_RULE_SET = "alpha.core-loop.v1"


def _alpha_decision(evidence: EvidenceInput) -> Decision:
    """Immediate Alpha policy: require non-empty uri and hash."""
    uri = (evidence.uri or "").strip()
    digest = (evidence.hash or "").strip()
    if not uri or not digest:
        return "rejected"
    if uri.startswith("s3://") or uri.startswith("https://") or uri.startswith("file://"):
        return "approved"
    return "pending"


def submit_validation(
    db: Session,
    *,
    asset_id: uuid.UUID,
    evidence_id: uuid.UUID,
    evidence_input: EvidenceInput,
) -> tuple[uuid.UUID, Decision]:
    """POST validation/v1/validations equivalent."""
    decision = _alpha_decision(evidence_input)
    row = ValidationRecord(
        asset_id=asset_id,
        evidence_id=evidence_id,
        decision=decision,
        rule_set=ALPHA_RULE_SET,
    )
    db.add(row)
    db.flush()
    return row.id, decision


def get_evidence_row(db: Session, evidence_id: uuid.UUID) -> Evidence | None:
    return db.get(Evidence, evidence_id)
