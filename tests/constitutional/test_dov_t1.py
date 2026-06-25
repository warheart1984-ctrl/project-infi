"""Tests for DOV-T1 dual-origin validation and related JPSS experiments."""

from __future__ import annotations

from datetime import UTC, datetime

from constitutional.jpss.convergence_experiment import (
    ConvergenceParticipant,
    RawConvergenceResponse,
    classify_convergence_insight,
    summarize_convergence,
)
from constitutional.jpss.dual_origin_validation import DualOriginInsight, evaluate_dov_t1
from constitutional.jpss.propagation_convergence_growth import (
    SignalEvent,
    assess_balanced_growth,
    compute_growth_curve,
)
from constitutional.jpss.reality_tracking_stress import (
    ToySystem,
    evaluate_reality_tracking,
    simulate_system,
)


def _passing_insights() -> list[DualOriginInsight]:
    propagation = [
        DualOriginInsight(
            id=f"p{i}",
            source_id=f"exposed-{i}",
            domain="ops",
            exposed_to_jpss=True,
            lineage_compatible=True,
            bidirectional=i == 0,
            grammar_tags=["drift", "threshold"],
        )
        for i in range(3)
    ]
    convergence = [
        DualOriginInsight(
            id="c1",
            source_id="naive-1",
            domain="biology",
            exposed_to_jpss=False,
            lineage_compatible=True,
            grammar_tags=["drift", "judgment"],
        ),
        DualOriginInsight(
            id="c2",
            source_id="naive-2",
            domain="finance",
            exposed_to_jpss=False,
            lineage_compatible=True,
            grammar_tags=["threshold", "preservation"],
        ),
    ]
    return propagation + convergence


def test_dov_t1_passes_when_all_criteria_met() -> None:
    result = evaluate_dov_t1(_passing_insights())
    assert result.reached is True
    assert result.reasons == []
    assert result.propagation_count == 3
    assert result.bidirectional_count == 1
    assert result.convergence_count == 2
    assert "drift" in result.shared_grammar_tokens


def test_dov_t1_fails_on_missing_bidirectional() -> None:
    insights = _passing_insights()
    for row in insights:
        row.bidirectional = False
    result = evaluate_dov_t1(insights)
    assert result.reached is False
    assert any("P2" in reason for reason in result.reasons)


def test_dov_t1_fails_on_incompatible_fork() -> None:
    insights = _passing_insights()
    insights[0].incompatible_fork = True
    result = evaluate_dov_t1(insights)
    assert result.reached is False
    assert any("K2" in reason for reason in result.reasons)


def test_convergence_experiment_classifies_unexposed_drift_language() -> None:
    participant = ConvergenceParticipant(id="p1", domain="ecology", prior_jpss_exposure=False)
    response = RawConvergenceResponse(
        participant_id="p1",
        text="Systems lose their way through slow drift past a hidden threshold.",
    )
    classified = classify_convergence_insight(response, participant)
    assert classified.classification == "CONVERGENCE"
    summary = summarize_convergence([classified])
    assert summary.convergence_count == 1
    assert summary.convergence_domains == ["ecology"]


def test_convergence_experiment_noise_when_jpss_exposed() -> None:
    participant = ConvergenceParticipant(id="p2", domain="law", prior_jpss_exposure=True)
    response = RawConvergenceResponse(
        participant_id="p2",
        text="Silent drift and calibration thresholds matter.",
    )
    classified = classify_convergence_insight(response, participant)
    assert classified.classification == "NOISE"


def test_growth_curve_and_balance() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    t1 = datetime(2026, 2, 1, tzinfo=UTC)
    t2 = datetime(2026, 3, 1, tzinfo=UTC)
    curve = compute_growth_curve(
        [
            SignalEvent(timestamp=t0, type="PROPAGATION"),
            SignalEvent(timestamp=t1, type="CONVERGENCE"),
            SignalEvent(timestamp=t2, type="PROPAGATION"),
        ]
    )
    assert len(curve) == 3
    assert curve[-1].propagation_count == 2
    assert curve[-1].convergence_count == 1
    assert assess_balanced_growth(curve).balanced is True


def test_reality_tracking_stress_mse() -> None:
    systems = [
        ToySystem(id="s1", invariant_value=0.0, drift_per_step=1.0, failure_threshold=10.0),
        ToySystem(id="s2", invariant_value=2.0, drift_per_step=0.5, failure_threshold=8.0),
    ]
    for system in systems:
        outcome = simulate_system(system)
        assert outcome.actual_failure_step >= 1

    evaluation = evaluate_reality_tracking(systems)
    assert evaluation.mse >= 0.0
    assert len(evaluation.details) == 2
