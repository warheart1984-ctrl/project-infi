"""Claim registry Explorer API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.dashboard import claims_queries

router = APIRouter(prefix="/claims", tags=["Claims"])


class ClaimRecord(BaseModel):
    id: str
    kind: str
    summary: str
    description: str | None = None
    subject_id: str | None = None
    subject_type: str | None = None
    created_at: str
    created_by: str
    status: str
    tier: str | None = None
    notes: str | None = None


class ClaimEvidenceLink(BaseModel):
    id: int
    claim_id: str
    pel_id: str
    relation: str
    strength: str
    created_at: str
    created_by: str


class ClaimGap(BaseModel):
    claim_id: str
    kind: str
    summary: str | None = None
    created_at: str | None = None
    created_by: str | None = None
    status: str | None = None
    tier: str | None = None
    missing_primary_evidence: bool = True


def _db_error(exc: FileNotFoundError) -> HTTPException:
    return HTTPException(status_code=500, detail=str(exc))


@router.get("/gaps/claims", response_model=list[ClaimGap])
def list_claims_missing_primary_evidence() -> list[ClaimGap]:
    """Active governed claims with no primary supporting PEL evidence link."""
    try:
        gaps = claims_queries.list_governed_claim_gaps()
    except FileNotFoundError as exc:
        raise _db_error(exc) from exc
    return [ClaimGap(**gap) for gap in gaps]


@router.get("", response_model=list[ClaimRecord])
def list_claims(
    kind: str | None = None,
    status: str | None = None,
    subject_id: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[ClaimRecord]:
    try:
        rows = claims_queries.list_claims(kind=kind, status=status, subject_id=subject_id, limit=limit)
    except FileNotFoundError as exc:
        raise _db_error(exc) from exc
    return [ClaimRecord(**row) for row in rows]


@router.get("/{claim_id}", response_model=ClaimRecord)
def get_claim(claim_id: str) -> ClaimRecord:
    try:
        row = claims_queries.get_claim(claim_id)
    except FileNotFoundError as exc:
        raise _db_error(exc) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    return ClaimRecord(**row)


@router.get("/{claim_id}/evidence", response_model=list[ClaimEvidenceLink])
def get_claim_evidence_links(claim_id: str) -> list[ClaimEvidenceLink]:
    try:
        claim = claims_queries.get_claim(claim_id)
        if claim is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        links = claims_queries.evidence_links_for_claim(claim_id)
    except FileNotFoundError as exc:
        raise _db_error(exc) from exc
    return [ClaimEvidenceLink(**link) for link in links]
