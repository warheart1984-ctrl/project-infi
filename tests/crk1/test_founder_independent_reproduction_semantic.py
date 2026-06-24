"""CRK-1 Founder-Independent Reproduction Test — Semantic Layer (K7–K12)."""

from __future__ import annotations

import pytest

from src.crk1.founder_independent_semantic_audit import FounderIndependentSemanticAudit


@pytest.fixture
def prepared_substrate(runtime):
    """
    Continuity substrate prepared via public runtime APIs only.
    Simulates a future operator discovering state without founder documentation.
    """
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    prediction = runtime.generate_prediction(frame.id, evidence.id)
    outcome = runtime.realize_outcome_from_prediction(prediction.id)
    replayed = runtime.replay_outcome(outcome.id)
    runtime.update_interpretation(frame.id, replayed.id)
    return runtime


@pytest.fixture
def semantic_audit(prepared_substrate) -> FounderIndependentSemanticAudit:
    return FounderIndependentSemanticAudit(prepared_substrate)


def test_founder_independent_semantic_suite_passes(semantic_audit) -> None:
    report = semantic_audit.run_all()
    assert report.passed, report.summary()


def test_fit_1_interpretive_enumeration(semantic_audit) -> None:
    result = semantic_audit.test_1_interpretive_enumeration()
    assert result.passed, result.detail


def test_fit_2_prediction_binding_reconstruction(semantic_audit) -> None:
    result = semantic_audit.test_2_prediction_binding_reconstruction()
    assert result.passed, result.detail


def test_fit_3_monoculture_detection(semantic_audit) -> None:
    result = semantic_audit.test_3_monoculture_detection()
    assert result.passed, result.detail


def test_fit_4_adversarial_reconstruction(semantic_audit) -> None:
    result = semantic_audit.test_4_adversarial_reconstruction()
    assert result.passed, result.detail


def test_fit_5_interpretive_drift_replay(semantic_audit) -> None:
    result = semantic_audit.test_5_interpretive_drift_replay()
    assert result.passed, result.detail


def test_fit_6_semantic_exposure_metric(semantic_audit) -> None:
    result = semantic_audit.test_6_semantic_exposure_metric()
    assert result.passed, result.detail
