"""Pydantic contracts for /v1/runtime/core-loop."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AssetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=512)
    metadata: dict[str, Any] | None = None


class EvidenceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: str = Field(..., min_length=1, max_length=128)
    uri: str = Field(..., min_length=1, max_length=2048)
    hash: str = Field(..., min_length=1, max_length=128)


class CoreLoopRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=255)
    asset: AssetInput
    evidence: EvidenceInput


class CoreLoopResponse(BaseModel):
    subject_id: UUID
    asset_id: UUID
    evidence_id: UUID
    validation_id: UUID
    decision: Literal["approved", "rejected", "pending"]
    audit_id: UUID


class RuntimeErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class AuditRecordResponse(BaseModel):
    audit_id: UUID
    subject_id: UUID
    asset_id: UUID
    evidence_id: UUID
    validation_id: UUID
    decision: Literal["approved", "rejected", "pending"]
    loop_hash: str
    created_at: str
