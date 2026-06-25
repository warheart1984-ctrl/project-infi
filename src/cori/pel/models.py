"""Pydantic models for the Primary Evidence Ledger (PEL) — Alpha canonical schema."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class PELRecord(BaseModel):
    """PEL atomic unit: timestamped, immutable evidence artifact from a governed loop."""

    id: str = Field(default_factory=lambda: f"PEL-{uuid4()}")
    kind: str = "audit_record"
    primary_hash: str
    actor_ref: str
    object_ref: str
    evidence_ref: str
    validation_ref: str
    decision: Literal["approved", "rejected", "pending"]
    observed_at: datetime = Field(default_factory=_utc_now)
    raw: dict[str, Any]
    audit_id: str | None = None


class Claim(BaseModel):
    """Declarative governance statement backed by primary PEL evidence."""

    id: str = Field(default_factory=lambda: f"CLAIM-{uuid4()}")
    kind: str = "governance"
    summary: str
    description: str
    subject_id: str | None = None
    status: Literal["draft", "active", "revoked"] = "active"
    tier: str = "T1"
    created_at: datetime = Field(default_factory=_utc_now)


class VerificationRecord(BaseModel):
    """Mechanical verification outcome for a claim against a PEL record."""

    id: str = Field(default_factory=lambda: f"VERIF-{uuid4()}")
    claim_id: str
    pel_record_id: str
    status: Literal["verified", "failed"]
    method: str = "pel_verify.py@alpha"
    details: dict[str, Any] = Field(default_factory=dict)
    verified_at: datetime = Field(default_factory=_utc_now)
