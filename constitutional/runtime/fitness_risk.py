"""Reconstructability risk overlay — fitness audit → projected failure risk."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.runtime.reconstructability_fitness_runtime import (
    FITNESS_STATE_ID,
    ReconstructabilityFitnessState,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

RECONSTRUCTABILITY_RISK_STATE_ID = "constitutional_risk__reconstructability"


class ReconstructabilityRiskState(BaseModel):
    """Fitness-derived reconstructability risk snapshot."""

    state_id: str = RECONSTRUCTABILITY_RISK_STATE_ID
    state_type: str = "constitutional_risk_reconstructability"
    snapshot_at: datetime
    reconstructability_risk: float = Field(ge=0.0, le=1.0)
    fitness_score: float = Field(ge=0.0, le=1.0)
    stewardship_readiness_score: float = Field(ge=0.0, le=1.0)


def load_reconstructability_risk(csr: ConstitutionalStateRuntime) -> ReconstructabilityRiskState | None:
    try:
        doc = csr.get_domain_doc(RECONSTRUCTABILITY_RISK_STATE_ID, ReconstructabilityRiskState)
        assert isinstance(doc, ReconstructabilityRiskState)
        return doc
    except KeyError:
        return None


def save_reconstructability_risk(
    csr: ConstitutionalStateRuntime,
    risk: ReconstructabilityRiskState,
) -> None:
    csr.put_domain_doc(RECONSTRUCTABILITY_RISK_STATE_ID, "constitutional_risk_reconstructability", risk)


def apply_fitness_to_risk(
    csr: ConstitutionalStateRuntime,
    rf_state: ReconstructabilityFitnessState,
    *,
    snapshot_at: datetime | None = None,
) -> ReconstructabilityRiskState:
    """v0: low fitness or readiness directly raise reconstructability_risk."""
    now = snapshot_at or datetime.now(UTC).replace(microsecond=0)
    reconstructability_risk = max(
        0.0,
        1.0 - min(rf_state.fitness_score, rf_state.stewardship_readiness_score),
    )
    risk = ReconstructabilityRiskState(
        snapshot_at=now,
        reconstructability_risk=reconstructability_risk,
        fitness_score=rf_state.fitness_score,
        stewardship_readiness_score=rf_state.stewardship_readiness_score,
    )
    save_reconstructability_risk(csr, risk)
    return risk


def get_reconstructability_fitness_state(
    csr: ConstitutionalStateRuntime,
) -> ReconstructabilityFitnessState:
    doc = csr.get_domain_doc(FITNESS_STATE_ID, ReconstructabilityFitnessState)
    assert isinstance(doc, ReconstructabilityFitnessState)
    return doc
