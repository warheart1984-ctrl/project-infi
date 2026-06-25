"""CE-1 continuity state vector CE(t) = (P, C, A) and compounding dominance."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEventLog


class ContinuityStateVector(BaseModel):
    """CE(t) = (P, C, A) — lineage state at time t."""

    timestamp: datetime
    propagation: int = Field(alias="P", default=0)
    convergence: int = Field(alias="C", default=0)
    accumulation: int = Field(alias="A", default=0)
    avg_chain_length: float = 0.0
    cross_domain_spread: int = 0

    model_config = {"populate_by_name": True}

    @property
    def P(self) -> int:
        return self.propagation

    @property
    def C(self) -> int:
        return self.convergence

    @property
    def A(self) -> int:
        return self.accumulation


class CompoundingDominanceAssessment(BaseModel):
    """A(t) growth vs P(t)+C(t) growth — compounding dominance condition."""

    dominance_holds: bool
    delta_propagation: int
    delta_convergence: int
    delta_accumulation: int
    explanation: str


def compute_state_vector(log: ContinuityEngineEventLog) -> ContinuityStateVector:
    from src.cos1.accumulation.chain_detector import (
        ClassifiedAccumulationEvent,
        detect_compounding_chains,
    )

    p = len(log.propagation_events())
    c = len(log.convergence_events())
    a = len(log.accumulation_events())

    classified = [
        ClassifiedAccumulationEvent(
            event_id=event.event_id,
            actor_id=event.actor.id,
            accumulation_signature=event.accumulation.signature,
            builds_on_event_ids=list(event.accumulation.builds_on_event_ids),
        )
        for event in log.accumulation_events()
    ]
    chains = detect_compounding_chains(classified)
    avg_chain = sum(chain.length for chain in chains) / len(chains) if chains else 0.0
    domains = {event.actor.domain for event in log.events}

    latest = max((event.timestamp for event in log.events), default=datetime.now())

    return ContinuityStateVector(
        timestamp=latest,
        propagation=p,
        convergence=c,
        accumulation=a,
        avg_chain_length=avg_chain,
        cross_domain_spread=len(domains),
    )


def assess_compounding_dominance(
    prior: ContinuityStateVector,
    current: ContinuityStateVector,
) -> CompoundingDominanceAssessment:
    delta_p = current.P - prior.P
    delta_c = current.C - prior.C
    delta_a = current.A - prior.A
    dominance = delta_a > (delta_p + delta_c)

    if dominance:
        explanation = (
            f"Compounding dominance: ΔA ({delta_a}) > ΔP+ΔC ({delta_p + delta_c}). "
            "Stewardship becomes increasingly likely."
        )
    else:
        explanation = (
            f"Compounding not yet dominant: ΔA ({delta_a}) ≤ ΔP+ΔC ({delta_p + delta_c})."
        )

    return CompoundingDominanceAssessment(
        dominance_holds=dominance,
        delta_propagation=delta_p,
        delta_convergence=delta_c,
        delta_accumulation=delta_a,
        explanation=explanation,
    )
