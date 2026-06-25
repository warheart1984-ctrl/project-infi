"""Transmission (propagation) and reality (convergence) axes for continuity validation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.jpss.dual_origin_validation import DualOriginInsight, evaluate_dov_t1
from constitutional.jpss.dov_t1_spec import DOV_T1_DEFINITION
from constitutional.jpss.propagation_convergence_growth import (
    GrowthPoint,
    SignalEvent,
    assess_balanced_growth,
    compute_growth_curve,
)
from src.continuity.stewardability.lineage_disambiguation import disambiguate_log
from src.continuity.stewardability.lineage_event_log import (
    REALITY_AXIS,
    TRANSMISSION_AXIS,
    LineageEvent,
    LineageEventLog,
    StructuralPrimitive,
)

CONVERGENCE_EVIDENCE_QUESTION = (
    "How many independent explanatory contributions from people with no JPSS exposure "
    "constitute evidence of convergence (reality-tracking)?"
)


class AxisAssessment(BaseModel):
    axis: str
    question: str
    signal_count: int
    domain_count: int
    bidirectional_count: int = 0
    notes: list[str] = Field(default_factory=list)


class DualAxesAssessment(BaseModel):
    transmission: AxisAssessment
    reality: AxisAssessment
    dov_reached: bool
    dov_reasons: list[str] = Field(default_factory=list)
    ambiguous_pending: int = 0
    growth_curve: list[GrowthPoint] = Field(default_factory=list)
    balanced_growth: bool = False


def _grammar_tags(alignment: list[StructuralPrimitive]) -> list[str]:
    mapping = {
        "threshold_shift": "threshold",
    }
    tags: list[str] = []
    for item in alignment:
        tags.append(mapping.get(item, item))
    return tags


def lineage_event_to_dual_origin(event: LineageEvent) -> DualOriginInsight | None:
    if event.origin.type not in ("PROPAGATION", "CONVERGENCE"):
        return None
    if event.origin.type == "DRIFT" or event.origin.type == "NOISE":
        return None
    return DualOriginInsight(
        id=event.event_id,
        source_id=event.actor.id,
        domain=event.actor.domain,
        exposed_to_jpss=event.actor.exposed_to_jpss,
        lineage_compatible=event.insight.lineage_compatible,
        bidirectional=event.propagation.bidirectional,
        grammar_tags=_grammar_tags(event.insight.structural_alignment),
        incompatible_fork=bool(event.origin.evidence.identity_breaking_divergence),
    )


def assess_dual_axes(log: LineageEventLog, *, disambiguate: bool = True) -> DualAxesAssessment:
    events = log.events
    if disambiguate:
        events, _ = disambiguate_log(events)

    propagation = [event for event in events if event.origin.type == "PROPAGATION"]
    convergence = [event for event in events if event.origin.type == "CONVERGENCE"]
    ambiguous = [event for event in events if event.origin.type == "AMBIGUOUS"]

    transmission = AxisAssessment(
        axis=TRANSMISSION_AXIS,
        question="Can JPSS ideas spread and generate new lineage-compatible insights?",
        signal_count=len(propagation),
        domain_count=len({event.actor.domain for event in propagation}),
        bidirectional_count=sum(1 for event in propagation if event.propagation.bidirectional),
        notes=[
            "Propagation measures lineage fertility (transmissibility), not truth.",
            f"{len(ambiguous)} ambiguous event(s) await disambiguation.",
        ]
        if ambiguous
        else ["Propagation measures lineage fertility (transmissibility), not truth."],
    )

    reality = AxisAssessment(
        axis=REALITY_AXIS,
        question="Do independent minds rediscover JPSS-compatible structures without exposure?",
        signal_count=len(convergence),
        domain_count=len({event.actor.domain for event in convergence}),
        notes=[
            "Convergence is the stronger claim — independent rediscovery suggests reality-tracking.",
            CONVERGENCE_EVIDENCE_QUESTION,
        ],
    )

    dov_insights = [
        row for event in events if (row := lineage_event_to_dual_origin(event)) is not None
    ]
    dov = evaluate_dov_t1(dov_insights)

    signal_events: list[SignalEvent] = []
    for event in events:
        if event.origin.type == "PROPAGATION":
            signal_events.append(SignalEvent(timestamp=event.timestamp, type="PROPAGATION"))
        elif event.origin.type == "CONVERGENCE":
            signal_events.append(SignalEvent(timestamp=event.timestamp, type="CONVERGENCE"))

    curve = compute_growth_curve(signal_events)
    balance = assess_balanced_growth(curve)

    return DualAxesAssessment(
        transmission=transmission,
        reality=reality,
        dov_reached=dov.reached,
        dov_reasons=dov.reasons,
        ambiguous_pending=len(ambiguous),
        growth_curve=curve,
        balanced_growth=balance.balanced,
    )


def dual_origin_validation_summary(log: LineageEventLog) -> str:
    assessment = assess_dual_axes(log)
    lines = [
        DOV_T1_DEFINITION,
        f"Transmission axis: {assessment.transmission.signal_count} propagation signal(s) "
        f"across {assessment.transmission.domain_count} domain(s).",
        f"Reality axis: {assessment.reality.signal_count} convergence signal(s) "
        f"across {assessment.reality.domain_count} domain(s).",
        f"DOV-T1 reached: {assessment.dov_reached}",
    ]
    if assessment.dov_reasons:
        lines.extend(f"  - {reason}" for reason in assessment.dov_reasons)
    return "\n".join(lines)
