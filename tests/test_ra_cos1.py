"""Tests for RA-COS-1, RASP-1, VAS-1, PSDD-1, and consequence-weighted invariants."""

from __future__ import annotations

from datetime import UTC, datetime

from src.continuity.ra import (
    AcceptanceEvent,
    RACOS1Runtime,
    SurpassmentCandidate,
    ValidationContext,
    apply_invariant_update,
    assess_psdd1,
    empty_ra_state,
    get_cbcl_ledger,
    post_acceptance_correction_loop,
    propose_change,
    record_consequence_sample,
    run_rag_loop,
    run_vas1_protocol,
    steward_approve_provisional_change,
    validate_change_vas1,
)
from src.continuity.stewardability.operating_conditions import good_conditions
from src.cos1.continuity_os import ContinuityOS


def test_vas1_requires_three_of_five_criteria() -> None:
    weak = validate_change_vas1(ValidationContext())
    assert weak.passed is False

    strong = validate_change_vas1(
        ValidationContext(
            predictive_accuracy_delta=0.1,
            explanatory_compression_delta=0.05,
            cross_domain_convergence=0.7,
            operational_outcome_delta=0.1,
            critique_stability=0.6,
        )
    )
    assert strong.passed is True
    assert len(strong.criteria_passed) >= 3


def test_psdd1_classifies_drift_bands() -> None:
    from src.continuity.ra.models import ConsequenceSample

    samples = [
        ConsequenceSample(
            change_id="chg-1",
            timestamp=datetime.now(UTC),
            metric="predictiveAccuracy",
            value=0.1,
        ),
        ConsequenceSample(
            change_id="chg-1",
            timestamp=datetime.now(UTC),
            metric="patchCount",
            value=0.9,
        ),
    ]
    assessment = assess_psdd1(samples, baseline=0.5)
    assert assessment.signals.aggregate_psd >= 0.0
    assert assessment.signals.classification in ("STABLE", "WATCH", "CRITICAL_REVIEW", "ROLLBACK")


def test_invariant_weight_moves_with_evidence() -> None:
    state = empty_ra_state()
    inv = state.invariants["K4"]
    up = apply_invariant_update(inv, 0.8)
    assert up.new_weight > up.prior_weight

    down = apply_invariant_update(inv, -0.8)
    assert down.new_weight < down.prior_weight


def test_rasp1_blocks_k4_violation() -> None:
    state = empty_ra_state()
    state = state.model_copy(update={"current_reconstruction_cost": 0.9})
    change = propose_change(
        "Structural deepening beyond threshold",
        reconstruction_cost_delta=0.5,
    )
    new_state, decision = steward_approve_provisional_change(state, change)
    assert decision.approved_provisional is False
    assert change.id not in new_state.changes


def test_rasp1_provisional_acceptance_registers_ledger() -> None:
    state = empty_ra_state()
    change = propose_change("Calibration drift guard extension")
    new_state, decision = steward_approve_provisional_change(state, change)
    assert decision.approved_provisional is True
    assert new_state.changes[change.id].status == "PROVISIONAL"
    assert new_state.ledger[change.id].validation_result == "PENDING"


def test_correction_loop_validates_stable_change() -> None:
    state = empty_ra_state()
    change = propose_change("Reality-anchored threshold shift")
    state, decision = steward_approve_provisional_change(state, change)
    assert decision.approved_provisional

    state = record_consequence_sample(state, change.id, "predictiveAccuracy", 0.8)
    state = record_consequence_sample(state, change.id, "operationalOutcome", 0.75)
    state = record_consequence_sample(state, change.id, "crossDomainConvergence", 0.7)

    state, result = post_acceptance_correction_loop(
        state,
        change.id,
        ValidationContext(
            predictive_accuracy_delta=0.1,
            explanatory_compression_delta=0.05,
            cross_domain_convergence=0.7,
            operational_outcome_delta=0.1,
            critique_stability=0.6,
        ),
    )
    assert result is not None
    assert result.new_status == "VALIDATED"
    assert state.changes[change.id].status == "VALIDATED"


def test_correction_loop_rolls_back_high_psd() -> None:
    state = empty_ra_state()
    change = propose_change("Overfitted extension")
    state, _ = steward_approve_provisional_change(state, change)

    for _ in range(3):
        state = record_consequence_sample(state, change.id, "patchCount", 2.0)
        state = record_consequence_sample(state, change.id, "predictiveAccuracy", 0.0)
        state = record_consequence_sample(state, change.id, "crossDomainConvergence", 0.0)
        state = record_consequence_sample(state, change.id, "operationalOutcome", 0.0)
        state = record_consequence_sample(state, change.id, "stewardLoad", 2.0)

    state, result = post_acceptance_correction_loop(
        state,
        change.id,
        ValidationContext(
            predictive_accuracy_delta=0.1,
            explanatory_compression_delta=0.05,
            cross_domain_convergence=0.7,
            operational_outcome_delta=0.1,
            critique_stability=0.6,
        ),
        baseline=0.5,
    )
    assert result is not None
    assert result.new_status == "ROLLED_BACK"
    assert result.spawn_revision is True


def test_ra_cos_runtime_processes_provisional_changes() -> None:
    runtime = RACOS1Runtime()
    change = propose_change("Successor surpassment integration")
    runtime, decision = runtime.propose_and_accept(change)
    assert decision.approved_provisional

    runtime.state = record_consequence_sample(
        runtime.state,
        change.id,
        "predictiveAccuracy",
        0.85,
    )
    cycle = runtime.run_cycle()
    assert cycle.provisional_processed == 1
    assert len(cycle.corrections) == 1


def test_cos1_step_includes_ra_cos1() -> None:
    os = ContinuityOS()
    result = os.step(good_conditions())
    assert result.ra_cos1 is not None
    assert result.ra_cos1.reference.startswith("Reality-Anchored")


def test_vas1_protocol_three_stages() -> None:
    surpassment = SurpassmentCandidate(
        insight_id="succ-1",
        explanatory_gain=0.4,
        integrates_primitives=["calibration", "drift", "grammar"],
        resolves_founder_limitation=True,
        survives_critique=True,
        accumulation_signature="A3",
    )
    acceptance = AcceptanceEvent(
        acknowledged_superiority=True,
        integrated_into_grammar=True,
        updated_invariants=True,
        relinquished_authority=True,
    )
    weak = run_vas1_protocol(surpassment, acceptance, ValidationContext())
    assert weak.stage1_surpassment.stage_met is True
    assert weak.stage2_acceptance.stage_met is True
    assert weak.validated is False
    assert weak.stage3_validation.reality_veto is True

    strong = run_vas1_protocol(
        surpassment,
        acceptance,
        ValidationContext(
            predictive_accuracy_delta=0.1,
            explanatory_compression_delta=0.05,
            cross_domain_convergence=0.7,
            operational_outcome_delta=0.1,
            critique_stability=0.6,
        ),
    )
    assert strong.validated is True


def test_vas1_rejects_accepted_without_reality() -> None:
    protocol = run_vas1_protocol(
        SurpassmentCandidate(
            insight_id="x",
            explanatory_gain=0.5,
            integrates_primitives=["a", "b"],
            resolves_founder_limitation=True,
            survives_critique=True,
            accumulation_signature="A4",
        ),
        AcceptanceEvent(
            acknowledged_superiority=True,
            integrated_into_grammar=True,
            updated_invariants=True,
            relinquished_authority=True,
        ),
        ValidationContext(),
    )
    assert protocol.stage2_acceptance.stage_met is True
    assert protocol.validated is False
    assert any("reality veto" in b.lower() for b in protocol.blockers)


def test_psdd1_reevaluation_and_rejection_thresholds() -> None:
    from src.continuity.ra.models import ConsequenceSample

    samples = [
        ConsequenceSample(
            change_id="c1",
            timestamp=datetime.now(UTC),
            metric="predictiveAccuracy",
            value=0.0,
        ),
        ConsequenceSample(
            change_id="c1",
            timestamp=datetime.now(UTC),
            metric="patchCount",
            value=1.5,
        ),
        ConsequenceSample(
            change_id="c1",
            timestamp=datetime.now(UTC),
            metric="stewardLoad",
            value=1.5,
        ),
    ]
    assessment = assess_psdd1(samples, baseline=0.5)
    assert assessment.flagged_for_reevaluation == (assessment.signals.aggregate_psd >= 0.6)
    assert assessment.rejected == (assessment.signals.aggregate_psd >= 0.8)


def test_rag_loop_full_cycle_validates() -> None:
    state = empty_ra_state()
    change = propose_change("Successor calibration guard")
    surpassment = SurpassmentCandidate(
        insight_id=change.id,
        explanatory_gain=0.5,
        integrates_primitives=["calibration", "drift"],
        resolves_founder_limitation=True,
        survives_critique=True,
        accumulation_signature="A3",
    )
    acceptance = AcceptanceEvent(
        acknowledged_superiority=True,
        integrated_into_grammar=True,
        updated_invariants=True,
        relinquished_authority=True,
    )
    ctx = ValidationContext(
        predictive_accuracy_delta=0.1,
        explanatory_compression_delta=0.05,
        cross_domain_convergence=0.7,
        operational_outcome_delta=0.1,
        critique_stability=0.6,
    )
    state, result, decision = run_rag_loop(state, change, surpassment, acceptance, ctx)
    assert decision is not None
    assert decision.approved_provisional is True
    assert result.vas_validated is True
    assert result.integrated is True
    assert len(result.cbcl_entries) == 1
    assert result.cbcl_entries[0].review_status == "Validated"


def test_cbcl_ledger_records_consequences() -> None:
    state = empty_ra_state()
    change = propose_change("Tracked improvement")
    state, _ = steward_approve_provisional_change(
        state,
        change,
        surpassment_evidence="A3 integrative synthesis",
        acceptance_evidence="FAP-1 founder acceptance",
    )
    state = record_consequence_sample(state, change.id, "predictiveAccuracy", 0.85)
    ledger = get_cbcl_ledger(state)
    assert len(ledger) == 1
    assert ledger[0].improvement_id == change.id
    assert ledger[0].surpassment_evidence.startswith("A3")
    assert ledger[0].review_status == "Under Review"
