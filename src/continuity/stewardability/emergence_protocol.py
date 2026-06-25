"""Steward Emergence Protocol — generate and recognize stewards by demonstrated capacity."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.capacity_test import StewardshipCapacityTestResult
from src.continuity.stewardability.register import (
    StewardAbilityRegister,
    StewardDemonstration,
    demonstration_context_from,
    record_event,
)

MIN_RECONSTRUCTIONS = 3


class EmergenceCandidate(BaseModel):
    id: str
    name: str
    background: str = ""


class EmergenceResult(BaseModel):
    candidate_id: str
    recognized_as_steward: bool
    reasons: list[str] = Field(default_factory=list)
    recorded_event_id: str


def run_steward_emergence_protocol(
    register: StewardAbilityRegister,
    candidate: EmergenceCandidate,
    demonstration: StewardDemonstration,
    *,
    capacity_test: StewardshipCapacityTestResult | None = None,
    require_capacity_test: bool = False,
) -> EmergenceResult:
    """Run exposure → demonstration → evaluation → recognition; record in register."""
    reasons: list[str] = []

    if require_capacity_test:
        if capacity_test is None or not capacity_test.passed:
            reasons.append("Stewardship Capacity Test not passed.")

    if len(demonstration.reconstructions) < MIN_RECONSTRUCTIONS:
        reasons.append("Insufficient reconstruction across continuity layers.")

    if not demonstration.critiques:
        reasons.append("No drift detection or critique demonstrated.")

    if demonstration.lineage_impact != "STRENGTHENED":
        reasons.append("Demonstration did not clearly strengthen lineage.")

    recognized = len(reasons) == 0
    context = demonstration_context_from(demonstration)
    notes = (
        f"Candidate {candidate.id} recognized as steward."
        if recognized
        else f"Candidate {candidate.id} not recognized as steward: {'; '.join(reasons)}"
    )

    event = record_event(
        register,
        kind="EMERGENCE" if recognized else "BLOCKAGE",
        context=context,
        demonstration=demonstration,
        notes=notes,
    )

    return EmergenceResult(
        candidate_id=candidate.id,
        recognized_as_steward=recognized,
        reasons=reasons,
        recorded_event_id=event.id,
    )
