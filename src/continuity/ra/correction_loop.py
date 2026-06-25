"""Post-acceptance correction loop — walk back or revise when reality disagrees."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from src.continuity.ra.cbcl1 import update_ledger_from_validation
from src.continuity.ra.invariant_update import InvariantUpdateResult, update_invariants_from_validation
from src.continuity.ra.models import (
    ChangeStatus,
    ConsequenceSample,
    LedgerEntry,
    LineageChange,
    RAState,
    ValidationContext,
)
from src.continuity.ra.psdd1 import assess_psdd1
from src.continuity.ra.vas1 import VAS1Result, validate_change_vas1


class CorrectionLoopResult(BaseModel):
    change_id: str
    prior_status: ChangeStatus
    new_status: ChangeStatus
    vas1: VAS1Result
    psd_classification: str
    invariant_updates: list[InvariantUpdateResult] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    spawn_revision: bool = False


def post_acceptance_correction_loop(
    state: RAState,
    change_id: str,
    validation_ctx: ValidationContext,
    *,
    baseline: float = 0.5,
) -> tuple[RAState, CorrectionLoopResult | None]:
    """
    Monitor → evaluate PSDD-1 → classify → act → log.

    PSD < 0.3 + VAS-1 pass → VALIDATED
    PSD ≥ 0.8 → ROLLED_BACK
    VAS-1 fail → REJECTED
    """
    change = state.changes.get(change_id)
    if change is None:
        return state, None

    ledger_entry = state.ledger.get(change_id)
    if ledger_entry is None:
        return state, None

    validation = validate_change_vas1(validation_ctx)
    relevant = [sample for sample in state.consequences if sample.change_id == change_id]
    psd = assess_psdd1(relevant, baseline)

    prior_status = change.status
    new_status: ChangeStatus = change.status
    notes = list(ledger_entry.notes)
    spawn_revision = False

    if not validation.passed:
        new_status = "REJECTED"
        notes.append("VAS-1 failed: reality veto — rejected even if accepted.")
        evidence = -0.5
    elif psd.rejected or psd.signals.classification == "ROLLBACK":
        new_status = "ROLLED_BACK"
        notes.append("High post-surpassment drift: rolled back.")
        spawn_revision = True
        evidence = -0.7
    elif psd.flagged_for_reevaluation or psd.signals.classification == "CRITICAL_REVIEW":
        notes.append("PSD ≥ 0.6: flagged for reality re-evaluation.")
        evidence = -0.3
    elif psd.signals.classification == "WATCH":
        notes.append("Elevated drift: watch window extended.")
        evidence = -0.1
    elif validation.passed and psd.signals.classification == "STABLE":
        new_status = "VALIDATED"
        notes.append("Validated by reality and stable over time.")
        evidence = 0.5
    else:
        evidence = 0.0

    now = datetime.now(UTC).replace(microsecond=0)
    updated_change = change.model_copy(
        update={
            "status": new_status,
            "validated_at": now if new_status == "VALIDATED" else change.validated_at,
        }
    )

    updated_ledger = update_ledger_from_validation(
        ledger_entry,
        vas1=validation,
        predictive_performance=validation_ctx.predictive_accuracy_delta,
        cross_domain_signals=(
            [f"convergence={validation_ctx.cross_domain_convergence:.2f}"]
            if validation_ctx.cross_domain_convergence > 0
            else []
        ),
        reconstructability_impact=change.reconstruction_cost_delta,
        steward_load_impact=max(0.0, psd.signals.load_spike),
        operational_outcomes=notes,
    )
    updated_ledger = updated_ledger.model_copy(
        update={
            "drift_signals": psd.signals,
            "final_status": new_status,
            "notes": notes,
        }
    )

    updated_invariants, inv_results = update_invariants_from_validation(
        state.invariants,
        change.affects_invariants,
        evidence,
    )

    reconstruction_cost = state.current_reconstruction_cost
    if new_status in ("REJECTED", "ROLLED_BACK"):
        reconstruction_cost = max(
            0.0,
            state.current_reconstruction_cost - change.reconstruction_cost_delta,
        )

    new_state = state.model_copy(
        update={
            "changes": {**state.changes, change_id: updated_change},
            "ledger": {**state.ledger, change_id: updated_ledger},
            "invariants": updated_invariants,
            "current_reconstruction_cost": reconstruction_cost,
        }
    )

    return new_state, CorrectionLoopResult(
        change_id=change_id,
        prior_status=prior_status,
        new_status=new_status,
        vas1=validation,
        psd_classification=psd.signals.classification,
        invariant_updates=inv_results,
        notes=notes,
        spawn_revision=spawn_revision,
    )


def record_consequence_sample(
    state: RAState,
    change_id: str,
    metric: str,
    value: float,
    *,
    timestamp: datetime | None = None,
) -> RAState:
    sample = ConsequenceSample(
        change_id=change_id,
        timestamp=timestamp or datetime.now(UTC).replace(microsecond=0),
        metric=metric,
        value=value,
    )
    return state.model_copy(update={"consequences": [*state.consequences, sample]})
