"""Tests for CRK-1 Semantic Reproduction Harness (K7–K12)."""

from __future__ import annotations

import pytest

from src.crk1.semantic_reproduction_harness import SemanticReproductionHarness


@pytest.fixture
def prepared_substrate(runtime, semantic_monitor):
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    prediction = runtime.generate_prediction(frame.id, evidence.id)
    outcome = runtime.realize_outcome_from_prediction(prediction.id)
    replayed = runtime.replay_outcome(outcome.id)
    runtime.update_interpretation(frame.id, replayed.id)
    runtime.get_reconstructions_for_evidence(evidence.id)
    semantic_monitor.snapshot()
    semantic_monitor.simulate_drift()
    return runtime, semantic_monitor


@pytest.fixture
def harness(prepared_substrate) -> SemanticReproductionHarness:
    runtime, monitor = prepared_substrate
    return SemanticReproductionHarness(runtime, monitor)


def test_semantic_reproduction_harness_passes(harness) -> None:
    results = harness.run()
    assert results["founder_independent_reproduction"] is True
    assert all(
        results[key]
        for key in (
            "K7_pluralism",
            "K8_prediction_binding",
            "K9_anti_monoculture",
            "K10_adversarial_reconstruction",
            "K11_drift_envelope",
            "K12_semantic_exposure",
        )
    )


def test_k11_drift_envelope_requires_history(runtime, semantic_monitor) -> None:
    harness = SemanticReproductionHarness(runtime, semantic_monitor)
    assert harness.test_drift_envelope() is False
    semantic_monitor.snapshot()
    semantic_monitor.simulate_drift()
    assert harness.test_drift_envelope() is True
