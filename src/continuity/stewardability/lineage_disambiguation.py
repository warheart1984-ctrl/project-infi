"""Disambiguate ambiguous lineage events into propagation, convergence, noise, or drift."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.stewardability.lineage_event_log import (
    LineageEvent,
    LineageOrigin,
    OriginType,
)

DisambiguationConfidence = Literal["LOW", "MEDIUM", "HIGH"]


class DisambiguationResult(BaseModel):
    event_id: str
    prior_type: OriginType
    resolved_type: OriginType
    confidence: DisambiguationConfidence = "LOW"
    reasons: list[str] = Field(default_factory=list)


def disambiguate_lineage_event(event: LineageEvent) -> tuple[LineageEvent, DisambiguationResult]:
    """
    Classify AMBIGUOUS concept-resonance inputs using exposure, novelty, and alignment.

    Concept resonance is the input; propagation or convergence is the classification.
    """
    prior = event.origin.type
    if prior != "AMBIGUOUS":
        return event, DisambiguationResult(
            event_id=event.event_id,
            prior_type=prior,
            resolved_type=prior,
            confidence="HIGH",
            reasons=["Origin already classified."],
        )

    evidence = event.origin.evidence
    reasons: list[str] = []

    if evidence.imitation_detected or event.insight.novelty_level == "ECHO":
        resolved: OriginType = "NOISE"
        reasons.append("Echo or imitation — not lineage signal.")
        confidence = "HIGH"
    elif evidence.identity_breaking_divergence:
        resolved = "DRIFT"
        reasons.append("Identity-breaking divergence detected.")
        confidence = "HIGH"
    elif not event.insight.lineage_compatible:
        resolved = "NOISE"
        reasons.append("Insight is not lineage-compatible.")
        confidence = "HIGH"
    elif event.actor.exposed_to_jpss and evidence.causal_influence_plausible is not False:
        resolved = "PROPAGATION"
        reasons.append("JPSS exposure with plausible causal influence — propagation axis.")
        confidence = "MEDIUM" if evidence.causal_influence_plausible is None else "HIGH"
    elif (
        not event.actor.exposed_to_jpss
        and evidence.no_exposure_confirmed
        and evidence.independent_derivation_plausible
        and event.insight.novelty_level in ("INDEPENDENT_EXPLANATION", "NEW_CONCEPT")
    ):
        resolved = "CONVERGENCE"
        reasons.append(
            "No JPSS exposure with independent explanatory novelty — reality axis (convergence)."
        )
        confidence = "HIGH"
    elif not event.actor.exposed_to_jpss and event.insight.lineage_compatible:
        resolved = "CONVERGENCE"
        reasons.append("Unexposed lineage-compatible insight — weak convergence signal.")
        confidence = "LOW"
    elif event.actor.exposed_to_jpss:
        resolved = "PROPAGATION"
        reasons.append("JPSS exposure present — weak propagation signal.")
        confidence = "LOW"
    else:
        resolved = "AMBIGUOUS"
        reasons.append("Insufficient evidence to resolve propagation vs convergence.")
        confidence = "LOW"

    updated = event.model_copy(
        update={
            "origin": LineageOrigin(
                type=resolved,
                possible=event.origin.possible,
                evidence=evidence,
            )
        }
    )
    return updated, DisambiguationResult(
        event_id=event.event_id,
        prior_type=prior,
        resolved_type=resolved,
        confidence=confidence,
        reasons=reasons,
    )


def disambiguate_log(events: list[LineageEvent]) -> tuple[list[LineageEvent], list[DisambiguationResult]]:
    resolved_events: list[LineageEvent] = []
    results: list[DisambiguationResult] = []
    for event in events:
        updated, result = disambiguate_lineage_event(event)
        resolved_events.append(updated)
        results.append(result)
    return resolved_events, results
