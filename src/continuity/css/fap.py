"""FAP-1 — Founder Acceptance Protocol."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.css.spec import FAP1_FORMULA

FAP1_REFERENCE = "Founder Acceptance Protocol FAP-1"


class FounderInsight(BaseModel):
    id: str
    text: str
    integration_score: float = 0.0


class SuccessorInsight(BaseModel):
    id: str
    actor_id: str
    text: str
    explanatory_gain: float = 0.0
    integration_score: float = 0.0
    accumulation_signature: str = "NONE"
    integrates_primitives: list[str] = Field(default_factory=list)
    survives_critique: bool = True


class FounderResponse(BaseModel):
    recognizes_successor: bool = False
    integrates_successor: bool = False
    updated_lineage: bool = False
    relinquished_authority: bool = False


class FAP1Assessment(BaseModel):
    reference: str = FAP1_REFERENCE
    formula: str = FAP1_FORMULA
    successor_surpasses_founder: bool = False
    founder_recognizes: bool = False
    founder_integrates: bool = False
    founder_relinquishes: bool = False
    founder_acceptance_met: bool = False
    blockers: list[str] = Field(default_factory=list)


def assess_fap1(
    founder: FounderInsight,
    successor: SuccessorInsight,
    response: FounderResponse,
) -> FAP1Assessment:
    surpasses = successor.integration_score > founder.integration_score
    if successor.explanatory_gain > 0 and successor.integration_score > founder.integration_score:
        surpasses = True

    blockers: list[str] = []
    if not surpasses:
        blockers.append("Successor insight does not exceed founder model (S > F).")
    if not response.recognizes_successor:
        blockers.append("Founder has not recognized successor insight.")
    if not response.integrates_successor:
        blockers.append("Founder has not integrated successor insight.")
    if not response.updated_lineage:
        blockers.append("Founder has not updated lineage accordingly.")
    if not response.relinquished_authority:
        blockers.append("Founder has not relinquished authority over the domain.")

    met = (
        surpasses
        and response.recognizes_successor
        and response.integrates_successor
        and response.updated_lineage
        and response.relinquished_authority
    )

    return FAP1Assessment(
        successor_surpasses_founder=surpasses,
        founder_recognizes=response.recognizes_successor,
        founder_integrates=response.integrates_successor,
        founder_relinquishes=response.relinquished_authority,
        founder_acceptance_met=met,
        blockers=blockers if not met else [],
    )
