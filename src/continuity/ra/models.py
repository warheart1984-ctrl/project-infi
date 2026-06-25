"""RA-COS-1 core types — invariants, changes, consequences, ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

InvariantStatus = Literal["ACTIVE", "UNDER_REVIEW", "DEPRECATED"]
ChangeStatus = Literal["PROVISIONAL", "VALIDATED", "REJECTED", "ROLLED_BACK"]
ValidationResult = Literal["PENDING", "PASSED", "FAILED"]
PSDClassification = Literal["STABLE", "WATCH", "CRITICAL_REVIEW", "ROLLBACK"]


class Invariant(BaseModel):
    id: str
    name: str
    description: str
    weight: float = Field(ge=0.0, le=1.0, default=0.5)
    impact: float = Field(ge=0.0, default=1.0)
    status: InvariantStatus = "ACTIVE"


class ChangeHypothesis(BaseModel):
    id: str
    description: str
    expected_effects: list[str] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    validation_window_days: int = 30
    rollback_conditions: list[str] = Field(default_factory=list)


class LineageChange(BaseModel):
    id: str
    description: str
    affects_invariants: list[str] = Field(default_factory=list)
    status: ChangeStatus = "PROVISIONAL"
    hypothesis: ChangeHypothesis
    reconstruction_cost_delta: float = 0.0
    reversible: bool = True
    respects_k1_k3: bool = True
    accepted_at: datetime | None = None
    validated_at: datetime | None = None


class ConsequenceSample(BaseModel):
    change_id: str
    timestamp: datetime
    metric: str
    value: float


class DriftSignals(BaseModel):
    predictive_divergence: float = 0.0
    explanatory_inflation: float = 0.0
    convergence_failure: float = 0.0
    operational_underperformance: float = 0.0
    load_spike: float = 0.0
    aggregate_psd: float = 0.0
    classification: PSDClassification = "STABLE"


class LedgerEntry(BaseModel):
    change_id: str
    surpassment_evidence: str = ""
    acceptance_evidence: str = ""
    validation_result: ValidationResult = "PENDING"
    operational_outcomes: list[str] = Field(default_factory=list)
    predictive_performance: float | None = None
    cross_domain_signals: list[str] = Field(default_factory=list)
    reconstructability_impact: float = 0.0
    steward_load_impact: float = 0.0
    drift_signals: DriftSignals | None = None
    final_status: ChangeStatus = "PROVISIONAL"
    notes: list[str] = Field(default_factory=list)


class ValidationContext(BaseModel):
    """VAS-1 validation inputs."""

    predictive_accuracy_delta: float = 0.0
    explanatory_compression_delta: float = 0.0
    cross_domain_convergence: float = 0.0
    operational_outcome_delta: float = 0.0
    critique_stability: float = 0.0


class RAState(BaseModel):
    invariants: dict[str, Invariant] = Field(default_factory=dict)
    changes: dict[str, LineageChange] = Field(default_factory=dict)
    consequences: list[ConsequenceSample] = Field(default_factory=list)
    ledger: dict[str, LedgerEntry] = Field(default_factory=dict)
    steward_load_max: float = 1.0
    reconstruction_cost_threshold: float = 1.0
    current_reconstruction_cost: float = 0.0
    current_steward_load: float = 0.0


def new_change_id(prefix: str = "chg") -> str:
    return f"{prefix}-{uuid4().hex[:10]}"


def default_invariants() -> dict[str, Invariant]:
    """K1–K4 invariants for reality-anchored governance."""
    return {
        "K1": Invariant(
            id="K1",
            name="Identity Coherence",
            description="Extensions remain recognizably part of the lineage.",
            weight=0.8,
            impact=1.0,
        ),
        "K2": Invariant(
            id="K2",
            name="Generative Grammar",
            description="Ideas carry structure that enables extension.",
            weight=0.75,
            impact=0.9,
        ),
        "K3": Invariant(
            id="K3",
            name="Integrability",
            description="New insights strengthen the lineage, not fragment it.",
            weight=0.75,
            impact=0.9,
        ),
        "K4": Invariant(
            id="K4",
            name="Reconstructability Protection",
            description="Reconstruction cost stays within configured threshold.",
            weight=0.85,
            impact=1.2,
        ),
    }


def empty_ra_state() -> RAState:
    return RAState(invariants=default_invariants())
