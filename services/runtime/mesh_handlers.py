"""In-process HTTP handlers backing the runtime mesh (identity/asset/evidence/validation)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.runtime.database import get_db, init_runtime_db
from src.runtime.schemas import AssetInput, EvidenceInput
from src.runtime.services.asset import create_asset
from src.runtime.services.evidence import attach_evidence
from src.runtime.services.identity import register_subject
from src.runtime.services.validation import submit_validation

mesh_router = APIRouter(prefix="/v1", tags=["runtime-mesh"])
_mesh_db_ready = False


def _ensure_db() -> None:
    global _mesh_db_ready
    if not _mesh_db_ready:
        init_runtime_db()
        _mesh_db_ready = True


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)


class RegisterResponse(BaseModel):
    subject_id: uuid.UUID


class AssetCreateRequest(BaseModel):
    subject_id: uuid.UUID
    type: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=512)
    metadata: dict[str, Any] | None = None


class AssetCreateResponse(BaseModel):
    asset_id: uuid.UUID


class EvidenceCreateRequest(BaseModel):
    asset_id: uuid.UUID
    kind: str = Field(..., min_length=1, max_length=128)
    uri: str = Field(..., min_length=1, max_length=2048)
    hash: str = Field(..., min_length=1, max_length=128)


class EvidenceCreateResponse(BaseModel):
    evidence_id: uuid.UUID


class ValidationCreateRequest(BaseModel):
    asset_id: uuid.UUID
    evidence_id: uuid.UUID
    evidence: dict[str, Any]


class ValidationCreateResponse(BaseModel):
    validation_id: uuid.UUID
    decision: str


@mesh_router.post("/register", response_model=RegisterResponse)
def register_subject_route(body: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    _ensure_db()
    subject_id = register_subject(db, email=str(body.email), display_name=body.display_name)
    db.commit()
    return RegisterResponse(subject_id=subject_id)


@mesh_router.post("/assets", response_model=AssetCreateResponse)
def create_asset_route(body: AssetCreateRequest, db: Session = Depends(get_db)) -> AssetCreateResponse:
    _ensure_db()
    asset = AssetInput(type=body.type, name=body.name, metadata=body.metadata)
    asset_id = create_asset(db, subject_id=body.subject_id, asset=asset)
    db.commit()
    return AssetCreateResponse(asset_id=asset_id)


@mesh_router.post("/evidence", response_model=EvidenceCreateResponse)
def create_evidence_route(body: EvidenceCreateRequest, db: Session = Depends(get_db)) -> EvidenceCreateResponse:
    _ensure_db()
    evidence = EvidenceInput(kind=body.kind, uri=body.uri, hash=body.hash)
    evidence_id = attach_evidence(db, asset_id=body.asset_id, evidence=evidence)
    db.commit()
    return EvidenceCreateResponse(evidence_id=evidence_id)


@mesh_router.post("/validations", response_model=ValidationCreateResponse)
def create_validation_route(
    body: ValidationCreateRequest,
    db: Session = Depends(get_db),
) -> ValidationCreateResponse:
    _ensure_db()
    try:
        evidence_input = EvidenceInput.model_validate(body.evidence)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid evidence payload: {exc}") from exc
    validation_id, decision = submit_validation(
        db,
        asset_id=body.asset_id,
        evidence_id=body.evidence_id,
        evidence_input=evidence_input,
    )
    db.commit()
    return ValidationCreateResponse(validation_id=validation_id, decision=decision)
