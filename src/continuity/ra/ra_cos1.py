"""RA-COS-1 — Reality-Anchored Continuity OS runtime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.ra.correction_loop import CorrectionLoopResult, post_acceptance_correction_loop
from src.continuity.ra.models import LineageChange, RAState, ValidationContext, empty_ra_state
from src.continuity.ra.rasp1 import RASP1Decision, steward_approve_provisional_change
from src.continuity.ra.spec import RA_COS1_REFERENCE


class RACOS1CycleResult(BaseModel):
    reference: str = RA_COS1_REFERENCE
    state: RAState
    provisional_processed: int = 0
    corrections: list[CorrectionLoopResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RACOS1Runtime:
    """RA-COS-1 governance loop over reality-anchored steward decisions."""

    def __init__(self, state: RAState | None = None) -> None:
        self.state = state or empty_ra_state()

    def propose_and_accept(
        self,
        change: LineageChange,
        *,
        surpassment_evidence: str = "",
        acceptance_evidence: str = "steward consensus",
    ) -> tuple[RACOS1Runtime, RASP1Decision]:
        new_state, decision = steward_approve_provisional_change(
            self.state,
            change,
            surpassment_evidence=surpassment_evidence,
            acceptance_evidence=acceptance_evidence,
        )
        self.state = new_state
        return self, decision

    def run_cycle(
        self,
        *,
        validation_by_change: dict[str, ValidationContext] | None = None,
        baseline: float = 0.5,
    ) -> RACOS1CycleResult:
        """
        RA-COS-1 main loop:
        for each provisional change → VAS-1 + PSDD-1 → correction loop → invariant update.
        """
        validation_by_change = validation_by_change or {}
        corrections: list[CorrectionLoopResult] = []
        notes: list[str] = []

        for change_id, change in list(self.state.changes.items()):
            if change.status != "PROVISIONAL":
                continue
            ctx = validation_by_change.get(
                change_id,
                ValidationContext(
                    predictive_accuracy_delta=0.1,
                    explanatory_compression_delta=0.05,
                    cross_domain_convergence=0.7,
                    operational_outcome_delta=0.1,
                    critique_stability=0.6,
                ),
            )
            self.state, result = post_acceptance_correction_loop(
                self.state,
                change_id,
                ctx,
                baseline=baseline,
            )
            if result is not None:
                corrections.append(result)
                notes.append(f"{change_id}: {result.prior_status} → {result.new_status}")

        return RACOS1CycleResult(
            state=self.state,
            provisional_processed=len(corrections),
            corrections=corrections,
            notes=notes,
        )
