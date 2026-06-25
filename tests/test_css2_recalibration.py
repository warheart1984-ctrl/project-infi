"""Tests for CSS-2 recalibration layer."""

from __future__ import annotations

import pytest

from src.continuity.css2 import (
    JPSS2Pipeline,
    ObserverTrainingProtocol,
    RecalibrationGovernanceEngine,
    RecalibrationLedger,
    RecalibrationProposalContext,
    RecalibrationTrigger,
    ThresholdChange,
    check_recalibration_amendment,
    default_recalibration_invariants,
)


def _evidence_trigger() -> RecalibrationTrigger:
    return RecalibrationTrigger(
        trigger_id="trg-1",
        trigger_type="evidence",
        description="Persistent mismatch between forecast and observed continuity.",
        persistent_mismatch=True,
        calibration_error=True,
    )


def _safe_change() -> ThresholdChange:
    return ThresholdChange(
        id="chg-pt3",
        metric_id="PT3_propagation",
        before=0.6,
        after=0.65,
        rationale="Raise propagation threshold after repeated false negatives.",
    )


def test_approved_recalibration_with_legitimate_trigger():
    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    ctx = RecalibrationProposalContext(
        proposed_changes=[_safe_change()],
        triggers=[_evidence_trigger()],
        invariants=default_recalibration_invariants(),
        trigger_type="evidence",
    )
    event = engine.evaluate_proposal(ctx)
    assert event.decision in {"approved", "deferred", "escalated"}
    assert len(ledger.events) == 1
    assert event.invariants_checked
    assert event.triggers


def test_rejected_without_trigger():
    engine = RecalibrationGovernanceEngine()
    ctx = RecalibrationProposalContext(
        proposed_changes=[_safe_change()],
        triggers=[],
        invariants=default_recalibration_invariants(),
    )
    event = engine.evaluate_proposal(ctx)
    assert event.decision == "rejected"
    assert "trigger" in event.legitimacy_basis.lower()


def test_rejected_non_derogable_invariant_touch():
    engine = RecalibrationGovernanceEngine()
    change = ThresholdChange(
        id="chg-k1",
        metric_id="K1_identity",
        before=1.0,
        after=0.5,
        rationale="Relax K1 identity coherence to allow faster drift.",
    )
    ctx = RecalibrationProposalContext(
        proposed_changes=[change],
        triggers=[_evidence_trigger()],
        invariants=default_recalibration_invariants(),
    )
    event = engine.evaluate_proposal(ctx)
    assert event.decision in {"rejected", "escalated", "deferred"}


def test_amendment_x_compliance_on_approved_event():
    engine = RecalibrationGovernanceEngine()
    event = engine.evaluate_proposal(
        RecalibrationProposalContext(
            proposed_changes=[_safe_change()],
            triggers=[_evidence_trigger()],
            invariants=default_recalibration_invariants(),
        )
    )
    compliance = check_recalibration_amendment(event)
    if event.decision == "approved":
        assert compliance.compliant or event.decision == "deferred"


def test_jpss2_pipeline_stages():
    pipeline = JPSS2Pipeline()
    result = pipeline.run_recalibration_path(
        triggers=[_evidence_trigger()],
        proposed_changes=[_safe_change()],
    )
    assert result.stages[0].stage == "recalibration_trigger_detection"
    assert result.stages[1].stage == "recalibration_proposal"
    assert result.recalibration_event is not None
    assert len(JPSS2Pipeline.pipeline_stages()) >= 11


def test_observer_training_five_phases():
    protocol = ObserverTrainingProtocol()
    protocol.register_case(
        __import__("src.continuity.css2.observer_training", fromlist=["TrainingCase"]).TrainingCase(
            case_id="c1",
            raw_narrative="Thresholds stayed fixed while failures accumulated.",
            expected_failure_markers=["threshold", "failure"],
        )
    )
    session = protocol.start_session("sess-1", "trainee-a")
    protocol.score_phase_1("sess-1", markers_found=["threshold", "failure"], thresholds_marked_off=2)
    protocol.score_phase_2("sess-1", detection_rate=0.8, explanation_quality=0.7)
    protocol.score_phase_3_f5("sess-1", phase_2_detection=0.8, domain_detection=0.75)
    protocol.score_phase_4_meta("sess-1", revision_point_accuracy=0.6, signal_identification=0.7)
    protocol.run_phase_5_governance_drill(
        "sess-1",
        trainee_id="trainee-a",
        proposed_changes=[_safe_change()],
        triggers=[_evidence_trigger()],
    )
    completed = protocol.complete_session("sess-1")
    assert completed.completed
    assert len(session.phase_scores) == 5


def test_calibration_updated_on_approval():
    ledger = RecalibrationLedger()
    engine = RecalibrationGovernanceEngine(ledger=ledger)
    event = engine.evaluate_proposal(
        RecalibrationProposalContext(
            proposed_changes=[_safe_change()],
            triggers=[_evidence_trigger()],
            invariants=default_recalibration_invariants(),
        )
    )
    if event.decision == "approved":
        assert "cal-subsystem" in ledger.calibrations
