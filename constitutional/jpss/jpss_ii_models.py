"""JPSS-II transferability models — no ECK-2 imports (breaks circular deps)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from constitutional.jpss.jpss_ii_spec import (
    JPSS_II_TRANSFERABILITY_LAW,
    JPSS_RECURSIVE_CONDITION,
)


class ValidityAxisScore(BaseModel):
    axis: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool = False
    evidence: list[str] = Field(default_factory=list)


class EvidenceTierScore(BaseModel):
    tier: str
    satisfied: bool = False
    detail: str = ""


class JPSSIITransferabilityReport(BaseModel):
    """JPSS subject to JPSS — recursive transferability evaluation."""

    recursive_condition: str = JPSS_RECURSIVE_CONDITION
    transferability_law: str = JPSS_II_TRANSFERABILITY_LAW
    epistemic_validity: ValidityAxisScore
    stewardship_validity: ValidityAxisScore
    evidence_tiers: list[EvidenceTierScore] = Field(default_factory=list)
    transferability_index: float = Field(default=0.0, ge=0.0, le=1.0)
    transferable: bool = False
    continuity_marks: dict[str, bool] = Field(default_factory=dict)
    captured_at: datetime | None = None
