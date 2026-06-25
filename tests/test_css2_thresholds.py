"""CSS-2 v0.2 — four operations, thresholds, recalibration governance."""

from __future__ import annotations

from src.continuity.crk1_threshold_amendment import (
    AMENDMENT_REFERENCE,
    STEWARDSHIP_DEFINITION,
    assess_crk1_threshold_amendment,
)
from src.continuity.css2 import (
    SystemState,
    Threshold,
    ThresholdDelta,
    apply_threshold,
    audit_threshold_registry,
    classify_operation,
    default_recalibration_rule,
    detect_hidden_recalibration,
    detect_recalibration_by_exception,
    detect_threshold_camouflage,
    evaluate_threshold_delta_legitimacy,
    run_jpss2_slice,
    seed_css1_thresholds,
)
from src.continuity.css2.jpss2_pipeline import MismatchSignal
from src.continuity.css2.operations import (
    test_a_learn_without_recalibrate as formal_test_a,
    test_b_recalibrate_without_learn as formal_test_b,
)
from src.continuity.css2.recalibration_governance import TeamAdversarialReview
from src.continuity.css2.spec import (
    FOUR_OPERATIONS,
    OPERATION_CALIBRATION,
    OPERATION_CONSTITUTIONAL_RECALIBRATION,
    OPERATION_LEARNING,
    OPERATION_RECALIBRATION,
)
from src.continuity.ra.recalibration_triggers import detect_recalibration_triggers


def test_four_operations_distinct():
    assert len(FOUR_OPERATIONS) == 4
    assert len(set(FOUR_OPERATIONS)) == 4


def test_classify_learning():
    result = classify_operation(belief_delta={"fact": "new pattern"})
    assert result.operation == OPERATION_LEARNING
    assert not result.threshold_changed


def test_classify_calibration():
    result = classify_operation(calibration_only=True)
    assert result.operation == OPERATION_CALIBRATION


def test_classify_recalibration():
    th = Threshold(
        name="t",
        domain="d",
        metric="m",
        comparator=">=",
        value=3,
        intent="test",
        owner="test",
    )
    after = th.model_copy(update={"value": 2})
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=after,
        rationale="intervene earlier",
    )
    result = classify_operation(threshold_delta=delta)
    assert result.operation == OPERATION_RECALIBRATION
    assert result.threshold_changed


def test_classify_constitutional_recalibration():
    from src.continuity.css2.threshold import RecalibrationRule, RecalibrationRuleDelta

    before = RecalibrationRule(name="r", who_may_propose=["steward"])
    after = before.model_copy(update={"who_may_propose": ["operator"]})
    delta = RecalibrationRuleDelta(
        rule_id=before.id,
        before=before,
        after=after,
        rationale="expand proposers",
    )
    result = classify_operation(rule_delta=delta)
    assert result.operation == OPERATION_CONSTITUTIONAL_RECALIBRATION


def test_a_learn_without_recalibrate():
    beliefs_before = {"model": "v1"}
    beliefs_after = {"model": "v2", "fact": "x"}
    th = seed_css1_thresholds()
    assert formal_test_a(
        beliefs_before=beliefs_before,
        beliefs_after=beliefs_after,
        thresholds_before=th,
        thresholds_after=th,
    )


def test_b_recalibrate_without_learn():
    th = seed_css1_thresholds()[0]
    after = th.model_copy(update={"value": th.value + 1})
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=after,
        rationale="tighter boundary",
    )
    beliefs = {"model": "v1"}
    assert formal_test_b(
        beliefs_before=beliefs,
        beliefs_after=beliefs,
        threshold_delta=delta,
    )


def test_apply_threshold_calibration():
    th = Threshold(
        name="drift",
        domain="PSDD-1",
        metric="psd_score",
        comparator=">=",
        value=0.6,
        intent="reeval",
        owner="RA",
    )
    assert apply_threshold(th, 0.5) == "normal"
    assert apply_threshold(th, 0.7) == "intervention"


def test_seed_css1_thresholds_audit_clean():
    thresholds = seed_css1_thresholds()
    report = audit_threshold_registry(thresholds)
    assert report.ok
    assert len(thresholds) >= 9


def test_recalibration_triggers_drift():
    state = SystemState(thresholds=seed_css1_thresholds())
    event = {"metric": "psd_score", "domain": "PSDD-1", "value": 0.7}
    triggers = detect_recalibration_triggers(
        event,
        drift_signals={"psd_score": 0.65, "domain": "PSDD-1"},
        validation={},
        state=state,
    )
    assert any(t.reason == "drift_signal" for t in triggers)


def test_recalibration_triggers_misclassification():
    state = SystemState(thresholds=seed_css1_thresholds())
    th = state.thresholds[0]
    event = {"metric": th.metric, "domain": th.domain}
    triggers = detect_recalibration_triggers(
        event,
        drift_signals={},
        validation={"misclassification_count": 5, "metric": th.metric},
        state=state,
    )
    assert any(t.reason == "systematic_misclassification" for t in triggers)


def test_evaluate_delta_requires_adversarial_review():
    th = seed_css1_thresholds()[0]
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=th.model_copy(update={"value": th.value + 1}),
        rationale="evidence-backed",
    )
    result = evaluate_threshold_delta_legitimacy(delta)
    assert not result.legitimate
    assert any("Adversarial" in b for b in result.blockers)


def test_evaluate_delta_passes_with_reviews():
    th = seed_css1_thresholds()[0]
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=th.model_copy(update={"value": th.value + 1}),
        rationale="evidence-backed",
    )
    reviews = [
        TeamAdversarialReview(team=t, passed=True) for t in ("red", "blue", "black", "white", "gold")
    ]
    result = evaluate_threshold_delta_legitimacy(delta, adversarial_results=reviews)
    assert result.legitimate


def test_hidden_recalibration_detection():
    th = seed_css1_thresholds()[0]
    mutated = th.model_copy(update={"value": 999})
    findings = detect_hidden_recalibration([th], [mutated], registered_deltas=[])
    assert findings and findings[0].kind == "hidden_recalibration"


def test_threshold_camouflage():
    th = seed_css1_thresholds()[0]
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=th.model_copy(update={"value": 1}),
        rationale="x",
    )
    finding = detect_threshold_camouflage(
        claimed_operation="learning",
        belief_delta={"x": 1},
        threshold_delta=delta,
    )
    assert finding is not None
    assert finding.kind == "threshold_camouflage"


def test_recalibration_by_exception():
    finding = detect_recalibration_by_exception(5, threshold_id="th-x")
    assert finding is not None
    assert finding.kind == "recalibration_by_exception"


def test_jpss2_pipeline_governed_update():
    thresholds = seed_css1_thresholds()
    th = thresholds[0]
    state = SystemState(thresholds=thresholds, recalibration_rule=default_recalibration_rule())
    delta = ThresholdDelta(
        threshold_id=th.id,
        before=th,
        after=th.model_copy(update={"value": th.value + 1}),
        rationale="JPSS-2 proposal",
    )
    reviews = [
        TeamAdversarialReview(team=t, passed=True) for t in ("red", "blue", "black", "white", "gold")
    ]
    result = run_jpss2_slice(
        {"metric": th.metric, "domain": th.domain},
        state,
        observed_values={th.metric: th.value},
        mismatch_signals=[
            MismatchSignal(threshold_id=th.id, kind="late_intervention", detail="test")
        ],
        proposed_delta=delta,
        adversarial_results=reviews,
    )
    assert result.legitimacy is not None
    assert result.legitimacy.legitimate
    updated = next(t for t in result.thresholds_after if t.id == th.id)
    assert updated.value == th.value + 1


def test_crk1_amendment_stewardship():
    report = assess_crk1_threshold_amendment(seed_css1_thresholds())
    assert report.compliant
    assert "legitimacy" in report.stewardship.lower()
