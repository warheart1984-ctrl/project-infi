"""SEC-1 — Steward Emergence Detector."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.register import StewardAbilityRegister
from src.cos1.continuity_engine.thresholds import ContinuityThresholdsAssessment

SEC1_REFERENCE = "Steward Emergence Detector SED-1"
SED1_REFERENCE = SEC1_REFERENCE
SEC1_MIN_GOVERNANCE_EVENTS = 1
SEC1_MIN_GOVERNANCE_CONTRIBUTORS = 2


class GovernanceEvent(BaseModel):
    """Identity-preserving governance event (G)."""

    event_id: str
    resolver_id: str
    resolved_conflict: str
    preserved_invariants: list[str] = Field(default_factory=list)


class SEC1Assessment(BaseModel):
    reference: str = SEC1_REFERENCE
    formula: str = "SED = (PT_3 ∧ CT_2 ∧ MAT_3 ∧ G > 0)"
    pt3_met: bool = False
    ct2_met: bool = False
    mat3_met: bool = False
    governance_event_count: int = 0
    governance_contributor_count: int = 0
    steward_emergence_met: bool = False
    governance_events: list[GovernanceEvent] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


def extract_governance_events(register: StewardAbilityRegister) -> list[GovernanceEvent]:
    """
    Derive identity-preserving governance events from steward demonstrations.

    A governance event occurs when a contributor resolves conflict while strengthening lineage.
    """
    events: list[GovernanceEvent] = []
    for entry in register.events:
        demo = entry.demonstration
        if demo is None:
            continue
        if demo.lineage_impact != "STRENGTHENED":
            continue
        if not demo.critiques and not demo.adaptations:
            continue
        conflict = demo.critiques[0] if demo.critiques else "identity conflict resolved"
        events.append(
            GovernanceEvent(
                event_id=entry.id,
                resolver_id=demo.steward_id,
                resolved_conflict=conflict,
                preserved_invariants=["K1", "K2", "K3"],
            )
        )
    return events


def assess_sec1(
    thresholds: ContinuityThresholdsAssessment,
    register: StewardAbilityRegister,
) -> SEC1Assessment:
    governance = extract_governance_events(register)
    contributors = {event.resolver_id for event in governance}
    g_count = len(governance)

    blockers: list[str] = []
    if not thresholds.propagation.met:
        blockers.extend(thresholds.propagation.blockers)
    if not thresholds.convergence.met:
        blockers.extend(thresholds.convergence.blockers)
    if not thresholds.accumulation.met:
        blockers.extend(thresholds.accumulation.blockers)
    if g_count < SEC1_MIN_GOVERNANCE_EVENTS:
        blockers.append(
            f"Need at least {SEC1_MIN_GOVERNANCE_EVENTS} identity-preserving governance event(s)."
        )
    if len(contributors) < SEC1_MIN_GOVERNANCE_CONTRIBUTORS:
        blockers.append(
            f"Need at least {SEC1_MIN_GOVERNANCE_CONTRIBUTORS} contributors resolving conflicts."
        )

    met = (
        thresholds.propagation.met
        and thresholds.convergence.met
        and thresholds.accumulation.met
        and g_count >= SEC1_MIN_GOVERNANCE_EVENTS
        and len(contributors) >= SEC1_MIN_GOVERNANCE_CONTRIBUTORS
    )

    return SEC1Assessment(
        pt3_met=thresholds.propagation.met,
        ct2_met=thresholds.convergence.met,
        mat3_met=thresholds.accumulation.met,
        governance_event_count=g_count,
        governance_contributor_count=len(contributors),
        steward_emergence_met=met,
        governance_events=governance,
        blockers=blockers if not met else [],
    )


# Alias for final-form naming
assess_sed1 = assess_sec1
