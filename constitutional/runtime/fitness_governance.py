"""Fitness governance gate — block or warn when reconstructability is too fragile."""

from __future__ import annotations

from pydantic import BaseModel

from constitutional.runtime.reconstructability_fitness_runtime import ReconstructabilityFitnessState
from constitutional.runtime.runtime import ConstitutionalStateRuntime

FITNESS_GOVERNANCE_STATE_ID = "fitness_governance_gate__latest"


class FitnessGovernanceDecision(BaseModel):
    """Outcome of evaluating reconstructability fitness for high-impact operations."""

    allow: bool
    level: str  # "ok" | "warn" | "block"
    reason: str


def evaluate_fitness_governance_gate(
    rf_state: ReconstructabilityFitnessState,
) -> FitnessGovernanceDecision:
    if rf_state.fitness_score < 0.4 or rf_state.stewardship_readiness_score < 0.3:
        return FitnessGovernanceDecision(
            allow=False,
            level="block",
            reason="Reconstructability fitness too low for high-impact changes",
        )

    if rf_state.fitness_score < 0.6 or rf_state.stewardship_readiness_score < 0.5:
        return FitnessGovernanceDecision(
            allow=True,
            level="warn",
            reason="Reconstructability degraded; proceed with explicit awareness",
        )

    return FitnessGovernanceDecision(
        allow=True,
        level="ok",
        reason="Reconstructability fitness within safe band",
    )


def apply_fitness_to_governance_gate(
    csr: ConstitutionalStateRuntime,
    rf_state: ReconstructabilityFitnessState,
) -> FitnessGovernanceDecision:
    decision = evaluate_fitness_governance_gate(rf_state)
    csr.put_domain_doc(FITNESS_GOVERNANCE_STATE_ID, "fitness_governance_gate", decision)
    return decision


def load_fitness_governance_decision(
    csr: ConstitutionalStateRuntime,
) -> FitnessGovernanceDecision | None:
    try:
        doc = csr.get_domain_doc(FITNESS_GOVERNANCE_STATE_ID, FitnessGovernanceDecision)
        assert isinstance(doc, FitnessGovernanceDecision)
        return doc
    except KeyError:
        return None
