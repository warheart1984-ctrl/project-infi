"""Reputation runtime — state documents and receipt kinds."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RUNTIME_NAME = "ReputationRuntime"

ReputationEventReceiptKind = Literal["Mention", "Endorsement", "Critique", "MisalignmentFlag"]
StatementReceiptKind = Literal["Publish", "Retract", "Clarify"]


class ReputationAssetStateDoc(BaseModel):
    state_type: Literal["ReputationAssetState"] = "ReputationAssetState"
    asset_id: str
    type: str
    impact: str = "medium"


class PublicStatementStateDoc(BaseModel):
    state_type: Literal["PublicStatementState"] = "PublicStatementState"
    statement_id: str
    channel: str
    topic: str
    alignment_with_invariants: bool = True


class ReferenceStateDoc(BaseModel):
    state_type: Literal["ReferenceState"] = "ReferenceState"
    reference_id: str
    source: str
    strength: float = Field(default=0.5, ge=0.0, le=1.0)


class ReputationProfileStateDoc(BaseModel):
    state_type: Literal["ReputationProfileState"] = "ReputationProfileState"
    profile_id: str
    domains: list[str] = Field(default_factory=list)
    credibility_scores: dict[str, float] = Field(default_factory=dict)
