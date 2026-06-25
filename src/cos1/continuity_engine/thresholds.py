"""CE-1 axis thresholds — PT-3, CT-2, MAT-3, and Continuity Mode."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.cos1.accumulation.chain_detector import (
    ClassifiedAccumulationEvent,
    CompoundingChain,
    detect_compounding_chains,
)
from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEventLog
from src.cos1.continuity_engine.spec import (
    CT2_MIN_CONVERGENCE,
    CT2_MIN_DOMAINS,
    MAT3_MIN_ACCUMULATION,
    PT3_MIN_PROPAGATION,
)


class AxisThresholdResult(BaseModel):
    axis: str
    threshold_id: str
    met: bool
    count: int
    required: int
    domain_count: int = 0
    blockers: list[str] = Field(default_factory=list)


class ContinuityThresholdsAssessment(BaseModel):
    propagation: AxisThresholdResult
    convergence: AxisThresholdResult
    accumulation: AxisThresholdResult
    continuity_mode: bool
    blockers: list[str] = Field(default_factory=list)


def assess_pt3(log: ContinuityEngineEventLog) -> AxisThresholdResult:
    events = log.propagation_events()
    count = len(events)
    met = count >= PT3_MIN_PROPAGATION
    blockers: list[str] = []
    if not met:
        blockers.append(
            f"Need {PT3_MIN_PROPAGATION - count} more propagation event(s) (PT-3)."
        )
    return AxisThresholdResult(
        axis="propagation",
        threshold_id="PT-3",
        met=met,
        count=count,
        required=PT3_MIN_PROPAGATION,
        domain_count=len({event.actor.domain for event in events}),
        blockers=blockers,
    )


def assess_ct2(log: ContinuityEngineEventLog) -> AxisThresholdResult:
    events = log.convergence_events()
    domains = {event.actor.domain for event in events}
    count = len(events)
    met = count >= CT2_MIN_CONVERGENCE and len(domains) >= CT2_MIN_DOMAINS
    blockers: list[str] = []
    if count < CT2_MIN_CONVERGENCE:
        blockers.append(
            f"Need {CT2_MIN_CONVERGENCE - count} more convergence event(s) (CT-2)."
        )
    if len(domains) < CT2_MIN_DOMAINS:
        blockers.append(
            f"Need {CT2_MIN_DOMAINS - len(domains)} more domain(s) for CT-2."
        )
    return AxisThresholdResult(
        axis="convergence",
        threshold_id="CT-2",
        met=met,
        count=count,
        required=CT2_MIN_CONVERGENCE,
        domain_count=len(domains),
        blockers=blockers,
    )


def assess_mat3_ce1(log: ContinuityEngineEventLog) -> AxisThresholdResult:
    """
    MAT-3 (CE-1): ≥3 accumulation events, ≥1 A2/A3, ≥1 multi-person chain.
    """
    events = log.accumulation_events()
    count = len(events)
    has_a2_a3 = any(
        event.accumulation.signature in {"A2", "A3"} for event in events
    )

    classified = [
        ClassifiedAccumulationEvent(
            event_id=event.event_id,
            actor_id=event.actor.id,
            accumulation_signature=event.accumulation.signature,
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
        )
        for event in events
    ]
    chains = detect_compounding_chains(classified)
    multi_actor_chains = [chain for chain in chains if chain.multi_actor]

    blockers: list[str] = []
    if count < MAT3_MIN_ACCUMULATION:
        blockers.append(
            f"Need {MAT3_MIN_ACCUMULATION - count} more accumulation event(s) (MAT-3)."
        )
    if not has_a2_a3:
        blockers.append("Need at least one A2 (structural) or A3 (integrative) event.")
    if not multi_actor_chains:
        blockers.append("Need at least one multi-person compounding chain.")

    met = count >= MAT3_MIN_ACCUMULATION and has_a2_a3 and bool(multi_actor_chains)

    return AxisThresholdResult(
        axis="accumulation",
        threshold_id="MAT-3",
        met=met,
        count=count,
        required=MAT3_MIN_ACCUMULATION,
        blockers=blockers,
    )


def assess_continuity_thresholds(log: ContinuityEngineEventLog) -> ContinuityThresholdsAssessment:
    pt3 = assess_pt3(log)
    ct2 = assess_ct2(log)
    mat3 = assess_mat3_ce1(log)
    continuity_mode = pt3.met and ct2.met and mat3.met
    blockers: list[str] = []
    if not continuity_mode:
        blockers.extend(pt3.blockers)
        blockers.extend(ct2.blockers)
        blockers.extend(mat3.blockers)

    return ContinuityThresholdsAssessment(
        propagation=pt3,
        convergence=ct2,
        accumulation=mat3,
        continuity_mode=continuity_mode,
        blockers=blockers,
    )
