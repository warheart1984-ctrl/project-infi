"""RASP-1 — Reality-Anchored Steward Protocol."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.continuity.ra.models import (
    ChangeHypothesis,
    LedgerEntry,
    LineageChange,
    RAState,
    new_change_id,
)
from src.continuity.ra.spec import RASP1_REFERENCE, RASP_RESPONSIBILITIES


class LineageFitCheck(BaseModel):
    k1_k3_satisfied: bool
    violations: list[str] = Field(default_factory=list)


class ReconstructabilityCheck(BaseModel):
    k4_satisfied: bool
    projected_cost: float
    threshold: float
    violations: list[str] = Field(default_factory=list)


class ConsequenceModelCheck(BaseModel):
    has_hypothesis: bool
    has_metrics: bool
    has_rollback_conditions: bool
    satisfied: bool


class RASP1Decision(BaseModel):
    reference: str = RASP1_REFERENCE
    approved_provisional: bool
    lineage_fit: LineageFitCheck
    reconstructability: ReconstructabilityCheck
    consequence_model: ConsequenceModelCheck
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def check_lineage_fit(change: LineageChange) -> LineageFitCheck:
    violations: list[str] = []
    if not change.respects_k1_k3:
        violations.append("Change does not respect K1–K3 (identity, grammar, integrability).")
    for inv_id in change.affects_invariants:
        if inv_id in {"K1", "K2", "K3"} and not change.respects_k1_k3:
            violations.append(f"Change threatens invariant {inv_id}.")
    return LineageFitCheck(k1_k3_satisfied=not violations, violations=violations)


def check_reconstructability(change: LineageChange, state: RAState) -> ReconstructabilityCheck:
    projected = state.current_reconstruction_cost + change.reconstruction_cost_delta
    threshold = state.reconstruction_cost_threshold
    violations: list[str] = []
    if projected > threshold:
        violations.append(
            f"K4 violated: projected reconstruction cost {projected:.2f} > threshold {threshold:.2f}."
        )
    if not change.reversible:
        violations.append("R3 violated: change is not reversible.")
    return ReconstructabilityCheck(
        k4_satisfied=not violations,
        projected_cost=projected,
        threshold=threshold,
        violations=violations,
    )


def check_consequence_model(hypothesis: ChangeHypothesis) -> ConsequenceModelCheck:
    has_hypothesis = bool(hypothesis.description.strip())
    has_metrics = bool(hypothesis.metrics)
    has_rollback = bool(hypothesis.rollback_conditions)
    satisfied = has_hypothesis and has_metrics and has_rollback
    return ConsequenceModelCheck(
        has_hypothesis=has_hypothesis,
        has_metrics=has_metrics,
        has_rollback_conditions=has_rollback,
        satisfied=satisfied,
    )


def evaluate_proposed_change(change: LineageChange, state: RAState) -> RASP1Decision:
    """RASP-1 steward decision protocol for proposed change Δ."""
    lineage = check_lineage_fit(change)
    recon = check_reconstructability(change, state)
    consequence = check_consequence_model(change.hypothesis)

    blockers: list[str] = []
    if not lineage.k1_k3_satisfied:
        blockers.extend(lineage.violations)
    if not recon.k4_satisfied:
        blockers.extend(recon.violations)
    if not consequence.satisfied:
        blockers.append("Missing consequence hypothesis, metrics, or rollback conditions.")
    if state.current_steward_load >= state.steward_load_max:
        blockers.append("Steward load at capacity — defer structural change.")

    approved = not blockers
    notes = [
        "Approved as PROVISIONAL only — not final until VAS-1 passes.",
        f"Validation window: {change.hypothesis.validation_window_days} days.",
    ] if approved else []

    return RASP1Decision(
        approved_provisional=approved,
        lineage_fit=lineage,
        reconstructability=recon,
        consequence_model=consequence,
        blockers=blockers,
        notes=notes,
    )


def steward_approve_provisional_change(
    state: RAState,
    change: LineageChange,
    *,
    surpassment_evidence: str = "",
    acceptance_evidence: str = "steward consensus",
) -> tuple[RAState, RASP1Decision]:
    """
    RASP-1 hook: evaluate Δ and register provisional acceptance in consequence ledger.
    """
    decision = evaluate_proposed_change(change, state)
    if not decision.approved_provisional:
        return state, decision

    now = datetime.now(UTC).replace(microsecond=0)
    accepted = change.model_copy(update={"status": "PROVISIONAL", "accepted_at": now})
    ledger_entry = LedgerEntry(
        change_id=change.id,
        surpassment_evidence=surpassment_evidence,
        acceptance_evidence=acceptance_evidence,
        validation_result="PENDING",
        drift_signals=None,
        final_status="PROVISIONAL",
        notes=list(decision.notes),
    )

    new_state = state.model_copy(
        update={
            "changes": {**state.changes, change.id: accepted},
            "ledger": {**state.ledger, change.id: ledger_entry},
            "current_reconstruction_cost": decision.reconstructability.projected_cost,
        }
    )
    return new_state, decision


def propose_change(
    description: str,
    *,
    affects_invariants: list[str] | None = None,
    hypothesis: ChangeHypothesis | None = None,
    reconstruction_cost_delta: float = 0.0,
    reversible: bool = True,
    respects_k1_k3: bool = True,
) -> LineageChange:
    change_id = new_change_id()
    hyp = hypothesis or ChangeHypothesis(
        id=f"hyp-{change_id}",
        description=description,
        expected_effects=[],
        metrics=["predictiveAccuracy", "operationalOutcome"],
        validation_window_days=30,
        rollback_conditions=["VAS-1 failure", "PSD ≥ 0.8"],
    )
    return LineageChange(
        id=change_id,
        description=description,
        affects_invariants=affects_invariants or ["K1", "K2", "K3", "K4"],
        hypothesis=hyp,
        reconstruction_cost_delta=reconstruction_cost_delta,
        reversible=reversible,
        respects_k1_k3=respects_k1_k3,
    )


def format_rasp_responsibilities() -> str:
    lines = [f"=== {RASP1_REFERENCE} ===", ""]
    for idx, rule in enumerate(RASP_RESPONSIBILITIES, start=1):
        lines.append(f"R{idx} — {rule}")
    return "\n".join(lines)
