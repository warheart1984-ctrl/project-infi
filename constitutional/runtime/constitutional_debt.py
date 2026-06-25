"""Constitutional debt — structured threat profile over scalar debt_score."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass


DEBT_STATE_ID = "constitutional_debt__global"


class ConstitutionalDebtState(BaseModel):
    """System-level constitutional debt with active reconstructability threats."""

    state_id: str = DEBT_STATE_ID
    state_type: str = "constitutional_debt"
    debt_score: float = Field(ge=0.0, le=1.0)
    fitness_penalty: float = Field(default=0.0, ge=0.0, le=1.0)
    threats: list[ReconstructabilityFailureClass] = Field(default_factory=list)
    unresolved_divergences: int = Field(default=0, ge=0)
    missing_receipts: int = Field(default=0, ge=0)
    overdue_remediations: int = Field(default=0, ge=0)
    unobserved_amendments: int = Field(default=0, ge=0)
    closed_without_receipts: int = Field(default=0, ge=0)


def compute_constitutional_debt_threats(
    *,
    unresolved_divergences: int = 0,
    missing_receipts: int = 0,
    overdue_remediations: int = 0,
    unobserved_amendments: int = 0,
    closed_without_receipts: int = 0,
    replay_diverged: bool = False,
) -> list[ReconstructabilityFailureClass]:
    """Map governance counters to active R-F* threat classes."""
    threats: list[ReconstructabilityFailureClass] = []
    if missing_receipts > 0:
        threats.append(ReconstructabilityFailureClass.EVIDENCE_LOSS)
    if unresolved_divergences > 0 or replay_diverged:
        threats.append(ReconstructabilityFailureClass.LINEAGE_BREAK)
    if overdue_remediations > 0:
        threats.append(ReconstructabilityFailureClass.REMEDIATION_AMNESIA)
    if unobserved_amendments > 0:
        threats.append(ReconstructabilityFailureClass.LEARNING_AMNESIA)
    if closed_without_receipts > 0:
        threats.append(ReconstructabilityFailureClass.STATE_LOSS)
    if unobserved_amendments > 0 and overdue_remediations > 0:
        threats.append(ReconstructabilityFailureClass.ACCOUNTABILITY_EROSION)
    return _dedupe(threats)


def compute_personal_debt_threats(
    *,
    unexternalized_ideas: int = 0,
    burnout_warnings: int = 0,
    unexternalized_contexts: int = 0,
    missing_receipts: int = 0,
    overdue_remediations: int = 0,
    unresolved_divergences: int = 0,
) -> list[ReconstructabilityFailureClass]:
    """Personal constitutional debt threat vector (founder / continuity scope)."""
    threats: list[ReconstructabilityFailureClass] = []
    if unexternalized_ideas > 0 or unexternalized_contexts > 0:
        threats.append(ReconstructabilityFailureClass.EVIDENCE_LOSS)
        threats.append(ReconstructabilityFailureClass.LINEAGE_BREAK)
        threats.append(ReconstructabilityFailureClass.STEWARD_DISCONTINUITY)
    if burnout_warnings > 0:
        threats.append(ReconstructabilityFailureClass.STEWARD_DISCONTINUITY)
    if missing_receipts > 0:
        threats.append(ReconstructabilityFailureClass.EVIDENCE_LOSS)
    if unresolved_divergences > 0:
        threats.append(ReconstructabilityFailureClass.LINEAGE_BREAK)
    if overdue_remediations > 0:
        threats.append(ReconstructabilityFailureClass.REMEDIATION_AMNESIA)
    return _dedupe(threats)


def debt_score_from_threats(threats: list[ReconstructabilityFailureClass]) -> float:
    """Normalize active threat count to 0–1 (v0 heuristic)."""
    if not threats:
        return 0.0
    return min(1.0, len(threats) / 5.0)


def build_constitutional_debt_state(
    *,
    unresolved_divergences: int = 0,
    missing_receipts: int = 0,
    overdue_remediations: int = 0,
    unobserved_amendments: int = 0,
    closed_without_receipts: int = 0,
    replay_diverged: bool = False,
) -> ConstitutionalDebtState:
    threats = compute_constitutional_debt_threats(
        unresolved_divergences=unresolved_divergences,
        missing_receipts=missing_receipts,
        overdue_remediations=overdue_remediations,
        unobserved_amendments=unobserved_amendments,
        closed_without_receipts=closed_without_receipts,
        replay_diverged=replay_diverged,
    )
    return ConstitutionalDebtState(
        debt_score=debt_score_from_threats(threats),
        threats=threats,
        unresolved_divergences=unresolved_divergences,
        missing_receipts=missing_receipts,
        overdue_remediations=overdue_remediations,
        unobserved_amendments=unobserved_amendments,
        closed_without_receipts=closed_without_receipts,
    )


def compute_fitness_penalty(
    *,
    failed_surfaces: list[ReconstructabilityFailureClass],
    implicit_assumptions_required: int,
) -> float:
    """v0: each failed surface adds 0.05, each implicit assumption adds 0.03."""
    return min(
        1.0,
        0.05 * len(failed_surfaces) + 0.03 * implicit_assumptions_required,
    )


def load_constitutional_debt(csr: object) -> ConstitutionalDebtState:
    """Load persisted debt or return an empty baseline."""
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    if not isinstance(csr, ConstitutionalStateRuntime):
        raise TypeError("csr must be ConstitutionalStateRuntime")
    try:
        doc = csr.get_domain_doc(DEBT_STATE_ID, ConstitutionalDebtState)
        assert isinstance(doc, ConstitutionalDebtState)
        return doc
    except KeyError:
        return ConstitutionalDebtState(debt_score=0.0, fitness_penalty=0.0)


def save_constitutional_debt(csr: object, debt: ConstitutionalDebtState) -> None:
    from constitutional.runtime.runtime import ConstitutionalStateRuntime

    if not isinstance(csr, ConstitutionalStateRuntime):
        raise TypeError("csr must be ConstitutionalStateRuntime")
    csr.put_domain_doc(DEBT_STATE_ID, "constitutional_debt", debt)


def apply_fitness_to_debt(csr: object, rf_state: object) -> ConstitutionalDebtState:
    """Merge reconstructability fitness audit into constitutional debt."""
    from constitutional.runtime.reconstructability_fitness_runtime import (
        ReconstructabilityFitnessState,
    )

    if not isinstance(rf_state, ReconstructabilityFitnessState):
        raise TypeError("rf_state must be ReconstructabilityFitnessState")

    debt = load_constitutional_debt(csr)
    debt.debt_score = max(0.0, debt.debt_score - debt.fitness_penalty)

    fitness_penalty = compute_fitness_penalty(
        failed_surfaces=rf_state.failed_surfaces,
        implicit_assumptions_required=rf_state.implicit_assumptions_required,
    )
    debt.fitness_penalty = fitness_penalty
    debt.debt_score = min(1.0, debt.debt_score + fitness_penalty)

    merged = set(debt.threats)
    merged.update(rf_state.failed_surfaces)
    debt.threats = _dedupe(list(merged))

    save_constitutional_debt(csr, debt)
    return debt


def _dedupe(
    threats: list[ReconstructabilityFailureClass],
) -> list[ReconstructabilityFailureClass]:
    seen: set[ReconstructabilityFailureClass] = set()
    ordered: list[ReconstructabilityFailureClass] = []
    for threat in threats:
        if threat not in seen:
            seen.add(threat)
            ordered.append(threat)
    return ordered
