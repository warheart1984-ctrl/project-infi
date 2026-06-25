"""Evidence service — attach evidence to an asset."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from src.runtime.models import Evidence
from src.runtime.schemas import EvidenceInput


def attach_evidence(db: Session, *, asset_id: uuid.UUID, evidence: EvidenceInput) -> uuid.UUID:
    """POST evidence/v1/evidence equivalent."""
    row = Evidence(
        asset_id=asset_id,
        kind=evidence.kind,
        uri=evidence.uri,
        content_hash=evidence.hash,
    )
    db.add(row)
    db.flush()
    return row.id
