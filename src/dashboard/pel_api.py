"""PEL Explorer API — read-only forensic routes over data/pel.sqlite3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.dashboard import pel_queries

router = APIRouter(prefix="/pel", tags=["PEL"])


class PELRecord(BaseModel):
    id: str
    type: str
    title: str | None = None
    description: str | None = None
    source_uri: str | None = None
    hash: str | None = None
    payload_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    author: str | None = None
    steward_role: str | None = None
    links: list[dict[str, Any]] = Field(default_factory=list)
    evidence_strength: str | None = None
    verified: bool = False
    verified_by: str | None = None
    verified_at: str | None = None
    notes: str | None = None


class ClaimGap(BaseModel):
    claim_id: str
    title: str | None = None
    created_at: str | None = None
    author: str | None = None
    missing_primary_evidence: bool = True


def _pel_db_error(exc: FileNotFoundError) -> HTTPException:
    return HTTPException(status_code=500, detail=str(exc))


@router.get("/records", response_model=list[PELRecord])
def list_records(
    type: str | None = None,
    author: str | None = None,
    evidence_strength: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[PELRecord]:
    try:
        rows = pel_queries.list_pel_records(
            type_=type,
            author=author,
            evidence_strength=evidence_strength,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise _pel_db_error(exc) from exc
    return [PELRecord(**row) for row in rows]


@router.get("/record/{pel_id}", response_model=PELRecord)
def get_record(pel_id: str) -> PELRecord:
    try:
        row = pel_queries.get_pel_record(pel_id)
    except FileNotFoundError as exc:
        raise _pel_db_error(exc) from exc
    if not row:
        raise HTTPException(status_code=404, detail="PEL record not found")
    return PELRecord(**row)


@router.get("/claim/{claim_id}/evidence", response_model=list[PELRecord])
def get_primary_evidence_for_claim(claim_id: str) -> list[PELRecord]:
    try:
        record = pel_queries.get_pel_record(claim_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        if record["type"] != "claim":
            raise HTTPException(status_code=400, detail="PEL record is not a claim")
        rows = pel_queries.primary_evidence_for_claim(claim_id)
    except FileNotFoundError as exc:
        raise _pel_db_error(exc) from exc
    return [PELRecord(**row) for row in rows]


@router.get("/evidence/{pel_id}/claims", response_model=list[PELRecord])
def get_claims_supported_by_evidence(pel_id: str) -> list[PELRecord]:
    try:
        rows = pel_queries.claims_supported_by_evidence(pel_id)
    except FileNotFoundError as exc:
        raise _pel_db_error(exc) from exc
    if rows is None:
        raise HTTPException(status_code=404, detail="PEL record not found")
    return [PELRecord(**row) for row in rows]


@router.get("/gaps/claims", response_model=list[ClaimGap])
def list_claims_missing_primary_evidence() -> list[ClaimGap]:
    """Return claims with no primary evidence supporting them."""
    try:
        gaps = pel_queries.list_claims_missing_primary_evidence()
    except FileNotFoundError as exc:
        raise _pel_db_error(exc) from exc
    return [ClaimGap(**gap) for gap in gaps]
