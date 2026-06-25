"""FastAPI routes for the Alpha runtime core loop."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.runtime.core_loop import run_core_loop
from src.runtime.database import get_db, init_runtime_db
from src.runtime.schemas import (
    AuditRecordResponse,
    CoreLoopRequest,
    CoreLoopResponse,
    RuntimeErrorResponse,
)
from src.runtime.models import AuditRecord

router = APIRouter(prefix="/v1/runtime", tags=["runtime"])
audit_router = APIRouter(prefix="/v1", tags=["runtime"])
_runtime_db_ready = False


def _ensure_runtime_db() -> None:
    global _runtime_db_ready
    if not _runtime_db_ready:
        init_runtime_db()
        _runtime_db_ready = True


@router.post(
    "/core-loop",
    response_model=CoreLoopResponse,
    responses={
        400: {"model": RuntimeErrorResponse},
        500: {"model": RuntimeErrorResponse},
    },
    summary="Execute the Alpha governed core loop",
    description=(
        "Canonical orchestration contract: identity → asset → evidence → "
        "validation → audit. Single source of truth for the 0001 → 1000 → 1001 loop."
    ),
)
def core_loop_endpoint(
    body: CoreLoopRequest,
    db: Session = Depends(get_db),
) -> CoreLoopResponse:
    _ensure_runtime_db()
    try:
        return run_core_loop(db, body)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@audit_router.get("/audit/{audit_id}", response_model=AuditRecordResponse)
def get_audit_record(audit_id: UUID, db: Session = Depends(get_db)) -> AuditRecordResponse:
    _ensure_runtime_db()
    row = db.get(AuditRecord, audit_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Audit record not found")
    created = row.created_at
    created_at = (
        created.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if created is not None
        else ""
    )
    return AuditRecordResponse(
        audit_id=row.id,
        subject_id=row.subject_id,
        asset_id=row.asset_id,
        evidence_id=row.evidence_id,
        validation_id=row.validation_id,
        decision=row.decision,
        loop_hash=row.loop_hash,
        created_at=created_at,
    )
