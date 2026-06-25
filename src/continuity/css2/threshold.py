"""Threshold and ThresholdDelta — first-class continuity decision boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

ThresholdComparator = Literal[">", ">=", "<", "<=", "==", "!=", "in", "out"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Threshold(BaseModel):
    """Governed boundary mapping a condition space to a decision class."""

    id: str = Field(default_factory=lambda: f"th-{uuid4().hex[:12]}")
    name: str
    domain: str
    metric: str
    comparator: ThresholdComparator
    value: Any
    unit: str | None = None
    context: dict[str, Any] | None = None
    intent: str
    owner: str | None = None
    created_at: str = Field(default_factory=_utc_now_iso)
    created_by: str = "system"
    last_updated_at: str = Field(default_factory=_utc_now_iso)
    last_updated_by: str = "system"

    def applies_to(self, metric: str, domain: str | None = None) -> bool:
        if self.metric != metric:
            return False
        if domain is not None and self.domain != domain:
            return False
        return True

    def classify(self, observed: Any) -> bool:
        """Return True when observed value satisfies the threshold (boundary crossed)."""
        return _evaluate_comparator(self.comparator, observed, self.value)


class ThresholdDelta(BaseModel):
    """Minimal unit of recalibration — one threshold before → after."""

    threshold_id: str
    before: Threshold
    after: Threshold
    rationale: str
    proposed_at: str = Field(default_factory=_utc_now_iso)
    proposed_by: str = "system"

    @property
    def is_recalibration(self) -> bool:
        return self.before.model_dump() != self.after.model_dump(
            exclude={"last_updated_at", "last_updated_by"}
        )


class RecalibrationRule(BaseModel):
    """Who/when/how threshold changes are permitted."""

    id: str = Field(default_factory=lambda: f"rr-{uuid4().hex[:12]}")
    name: str
    who_may_propose: list[str] = Field(default_factory=lambda: ["steward"])
    who_may_approve: list[str] = Field(default_factory=lambda: ["steward"])
    requires_evidence: bool = True
    requires_adversarial_review: bool = True
    adversarial_teams: list[str] = Field(
        default_factory=lambda: ["red", "blue", "black", "white", "gold"]
    )
    non_derogable_invariants: list[str] = Field(default_factory=list)
    intent: str = ""
    created_at: str = Field(default_factory=_utc_now_iso)
    created_by: str = "system"


class RecalibrationRuleDelta(BaseModel):
    """Minimal unit of constitutional recalibration."""

    rule_id: str
    before: RecalibrationRule
    after: RecalibrationRule
    rationale: str
    proposed_at: str = Field(default_factory=_utc_now_iso)
    proposed_by: str = "system"


class SystemState(BaseModel):
    """State bag for threshold-aware pipelines."""

    thresholds: list[Threshold] = Field(default_factory=list)
    recalibration_rule: RecalibrationRule | None = None


def _evaluate_comparator(
    comparator: ThresholdComparator,
    observed: Any,
    boundary: Any,
) -> bool:
    if comparator == ">":
        return observed > boundary
    if comparator == ">=":
        return observed >= boundary
    if comparator == "<":
        return observed < boundary
    if comparator == "<=":
        return observed <= boundary
    if comparator == "==":
        return observed == boundary
    if comparator == "!=":
        return observed != boundary
    if comparator == "in":
        return observed in boundary
    if comparator == "out":
        return observed not in boundary
    raise ValueError(f"unknown comparator: {comparator}")
