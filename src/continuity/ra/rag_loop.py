"""RAG-Loop — Reality-Anchored Governance Loop."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.ra.cbcl1 import CBCL1Entry, get_cbcl_ledger, update_ledger_from_validation
from src.continuity.ra.correction_loop import CorrectionLoopResult, post_acceptance_correction_loop
from src.continuity.ra.models import LineageChange, RAState, ValidationContext
from src.continuity.ra.rasp1 import RASP1Decision, steward_approve_provisional_change
from src.continuity.ra.spec import (
    EPISTEMIC_INSIGHT,
    RAG_LOOP_REFERENCE,
    RAG_LOOP_STAGES,
    RAG_STAGE_ACCEPTANCE,
    RAG_STAGE_CORRECTION,
    RAG_STAGE_INTEGRATION,
    RAG_STAGE_MONITORING,
    RAG_STAGE_SURPASSMENT,
    RAG_STAGE_VALIDATION,
)
from src.continuity.ra.vas1 import (
    AcceptanceEvent,
    SurpassmentCandidate,
    run_vas1_protocol,
)


class RAGLoopResult(BaseModel):
    reference: str = RAG_LOOP_REFERENCE
    epistemic_insight: str = EPISTEMIC_INSIGHT
    stages: list[str] = Field(default_factory=list)
    current_stage: str = ""
    vas_validated: bool = False
    integrated: bool = False
    correction: CorrectionLoopResult | None = None
    cbcl_entries: list[CBCL1Entry] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def run_rag_loop(
    state: RAState,
    change: LineageChange,
    surpassment: SurpassmentCandidate,
    acceptance: AcceptanceEvent,
    validation_ctx: ValidationContext,
    *,
    baseline: float = 0.5,
    surpassment_evidence: str = "",
    acceptance_evidence: str = "",
) -> tuple[RAState, RAGLoopResult, RASP1Decision | None]:
    """
    Reality-Anchored Governance Loop:

    Surpassment → Acceptance → Validation → Integration → Monitoring → Correction
    """
    stages: list[str] = []
    blockers: list[str] = []
    notes: list[str] = [EPISTEMIC_INSIGHT]
    decision: RASP1Decision | None = None

    # Stage 1 — Surpassment
    stages.append(RAG_STAGE_SURPASSMENT)
    if not surpassment.stage_met:
        return state, RAGLoopResult(
            stages=stages,
            current_stage=RAG_STAGE_SURPASSMENT,
            blockers=["Surpassment candidate not qualified (SSDE-1)."],
            notes=notes,
        ), None

    # Stage 2 — Acceptance (provisional registration)
    stages.append(RAG_STAGE_ACCEPTANCE)
    if not acceptance.stage_met:
        return state, RAGLoopResult(
            stages=stages,
            current_stage=RAG_STAGE_ACCEPTANCE,
            blockers=["Lineage acceptance incomplete (FAP-1)."],
            notes=notes,
        ), None

    state, decision = steward_approve_provisional_change(
        state,
        change,
        surpassment_evidence=surpassment_evidence or f"SSDE candidate {surpassment.insight_id}",
        acceptance_evidence=acceptance_evidence or "FAP-1 acceptance recorded",
    )
    if decision is None or not decision.approved_provisional:
        blockers.extend(decision.blockers if decision else ["RASP-1 blocked provisional acceptance."])
        return state, RAGLoopResult(
            stages=stages,
            current_stage=RAG_STAGE_ACCEPTANCE,
            blockers=blockers,
            notes=notes,
        ), decision

    # Stage 3 — Validation (VAS-1 proper)
    stages.append(RAG_STAGE_VALIDATION)
    protocol = run_vas1_protocol(surpassment, acceptance, validation_ctx)
    if not protocol.validated and protocol.stage3_validation.reality_veto:
        notes.append("Reality veto: accepted improvement failed VAS-1.")

    # Stage 4–6 — Integration, Monitoring, Correction
    stages.extend([RAG_STAGE_INTEGRATION, RAG_STAGE_MONITORING, RAG_STAGE_CORRECTION])
    state, correction = post_acceptance_correction_loop(
        state,
        change.id,
        validation_ctx,
        baseline=baseline,
    )

    integrated = correction is not None and correction.new_status == "VALIDATED"
    if correction is not None:
        ledger = state.ledger.get(change.id)
        if ledger is not None:
            updated = update_ledger_from_validation(
                ledger,
                vas1=correction.vas1,
                predictive_performance=validation_ctx.predictive_accuracy_delta,
                cross_domain_signals=(
                    [f"convergence={validation_ctx.cross_domain_convergence:.2f}"]
                    if validation_ctx.cross_domain_convergence > 0
                    else []
                ),
                reconstructability_impact=change.reconstruction_cost_delta,
                steward_load_impact=state.current_steward_load,
            )
            state = state.model_copy(
                update={"ledger": {**state.ledger, change.id: updated}}
            )

    current_stage = RAG_STAGE_CORRECTION
    if integrated:
        notes.append("Validated improvement integrated into lineage invariants/grammar.")
    elif correction and correction.new_status == "REJECTED":
        notes.append("Rejected by reality despite acceptance.")
        blockers.append("VAS-1 reality veto after acceptance.")

    return state, RAGLoopResult(
        stages=stages,
        current_stage=current_stage,
        vas_validated=protocol.validated,
        integrated=integrated,
        correction=correction,
        cbcl_entries=get_cbcl_ledger(state),
        blockers=blockers,
        notes=notes,
    ), decision


def format_rag_loop() -> str:
    lines = [f"=== {RAG_LOOP_REFERENCE} ===", "", EPISTEMIC_INSIGHT, ""]
    for index, stage in enumerate(RAG_LOOP_STAGES, start=1):
        arrow = " → " if index < len(RAG_LOOP_STAGES) else ""
        lines.append(f"{index}. {stage}{arrow}")
    lines.append("(back to Surpassment)")
    return "\n".join(lines)
