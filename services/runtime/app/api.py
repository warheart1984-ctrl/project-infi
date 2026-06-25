"""FastAPI routes for the runtime mesh orchestrator."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.cori.pel.canonical import compute_loop_hash
from services.runtime.app.orchestrator import CoreLoopError, CoreLoopRequest, run_core_loop
from src.runtime.database import get_db, init_runtime_db
from src.runtime.models import AuditRecord

router = APIRouter(prefix="/v1/runtime", tags=["runtime"])
audit_router = APIRouter(prefix="/v1", tags=["runtime"])
_runtime_db_ready = False


class CoreLoopResponse(BaseModel):
    subject_id: UUID
    asset_id: UUID
    evidence_id: UUID
    validation_id: UUID
    decision: Literal["approved", "rejected", "pending"]
    audit_id: UUID


class AuditRequest(BaseModel):
    subject_id: UUID
    asset_id: UUID
    evidence_id: UUID
    validation_id: UUID
    decision: str = Field(..., min_length=1, max_length=32)
    loop_hash: str = Field(..., min_length=64, max_length=128)


class AuditResponse(BaseModel):
    audit_id: UUID


def _ensure_runtime_db() -> None:
    global _runtime_db_ready
    if not _runtime_db_ready:
        init_runtime_db()
        _runtime_db_ready = True


@router.post("/core-loop", response_model=CoreLoopResponse)
async def core_loop(payload: CoreLoopRequest) -> CoreLoopResponse:
    try:
        result = await run_core_loop(payload)
        return CoreLoopResponse(**result)
    except CoreLoopError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal runtime error") from exc


@audit_router.post("/audit", response_model=AuditResponse)
def post_audit(body: AuditRequest, db: Session = Depends(get_db)) -> AuditResponse:
    """Persist immutable audit record (called by the orchestrator)."""
    _ensure_runtime_db()
    expected = compute_loop_hash(
        subject_id=body.subject_id,
        asset_id=body.asset_id,
        evidence_id=body.evidence_id,
        validation_id=body.validation_id,
        decision=body.decision,
    )
    if body.loop_hash != expected:
        raise HTTPException(status_code=400, detail="loop_hash mismatch")

    row = AuditRecord(
        subject_id=body.subject_id,
        asset_id=body.asset_id,
        evidence_id=body.evidence_id,
        validation_id=body.validation_id,
        decision=body.decision,
        loop_hash=body.loop_hash,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AuditResponse(audit_id=row.id)
