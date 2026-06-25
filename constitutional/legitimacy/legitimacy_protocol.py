"""Stewardship Legitimacy Protocol — Competence, Receipts, Plurality."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

PROTOCOL_REFERENCE = "Stewardship Legitimacy Protocol"


class LegitimacyPillar(str, Enum):
    COMPETENCE = "Competence"
    RECEIPTS = "Receipts"
    PLURALITY = "Plurality"


COMPETENCE_REQUIREMENTS: tuple[str, ...] = (
    "jpss_judgment_exam",
    "jpss_i_adaptive_invariant_exam",
    "jpss_c_constitutional_exam",
    "constitutional_reasoning_reconstruction",
    "consequence_modeling",
)

RECEIPTS_REQUIREMENTS: tuple[str, ...] = (
    "decisions_recorded",
    "reasoning_reconstructable",
    "reasoning_criticizable",
    "survivable_by_future_stewards",
)

PLURALITY_REQUIREMENTS: tuple[str, ...] = (
    "distributed_certified_stewards",
    "overlapping_reconstruction_competence",
    "no_unilateral_invariant_alteration",
    "prior_cohort_certification",
)


class ProtocolPillarStatus(BaseModel):
    pillar: LegitimacyPillar
    satisfied: bool
    requirements_met: list[str] = Field(default_factory=list)
    requirements_missing: list[str] = Field(default_factory=list)


class StewardshipLegitimacyProtocolStatus(BaseModel):
    competence: ProtocolPillarStatus
    receipts: ProtocolPillarStatus
    plurality: ProtocolPillarStatus

    @property
    def satisfied(self) -> bool:
        return self.competence.satisfied and self.receipts.satisfied and self.plurality.satisfied


def evaluate_protocol_pillars(
    *,
    competence_met: list[str],
    receipts_met: list[str],
    plurality_met: list[str],
) -> StewardshipLegitimacyProtocolStatus:
    competence_missing = [r for r in COMPETENCE_REQUIREMENTS if r not in competence_met]
    receipts_missing = [r for r in RECEIPTS_REQUIREMENTS if r not in receipts_met]
    plurality_missing = [r for r in PLURALITY_REQUIREMENTS if r not in plurality_met]

    return StewardshipLegitimacyProtocolStatus(
        competence=ProtocolPillarStatus(
            pillar=LegitimacyPillar.COMPETENCE,
            satisfied=not competence_missing,
            requirements_met=competence_met,
            requirements_missing=competence_missing,
        ),
        receipts=ProtocolPillarStatus(
            pillar=LegitimacyPillar.RECEIPTS,
            satisfied=not receipts_missing,
            requirements_met=receipts_met,
            requirements_missing=receipts_missing,
        ),
        plurality=ProtocolPillarStatus(
            pillar=LegitimacyPillar.PLURALITY,
            satisfied=not plurality_missing,
            requirements_met=plurality_met,
            requirements_missing=plurality_missing,
        ),
    )
