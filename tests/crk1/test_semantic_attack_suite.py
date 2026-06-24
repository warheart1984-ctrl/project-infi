"""CRK-1 semantic layer attack suite — K7–K12 interpretive capture tests."""

from __future__ import annotations


def test_k7_no_single_interpretation(runtime) -> None:
    """K7: every evidence object has at least two interpretive pathways."""
    evidence = runtime.create_evidence()
    interpretations = runtime.get_interpretations(evidence.id)
    assert len(interpretations) >= 2


def test_k8_interpretations_are_prediction_bound(runtime) -> None:
    """K8: interpretive frames bind to testable predictions."""
    frame = runtime.get_dominant_interpretation()
    evidence = runtime.create_evidence()
    prediction = runtime.generate_prediction(frame.id, evidence.id)
    assert prediction is not None


def test_k8_interpretations_update_on_outcome(runtime) -> None:
    """K8: outcomes replay into evidence that updates frame credibility."""
    frame = runtime.get_dominant_interpretation()
    evidence = runtime.create_evidence()
    prediction = runtime.generate_prediction(frame.id, evidence.id)
    outcome = runtime.realize_outcome_from_prediction(prediction.id)
    replayed = runtime.replay_outcome(outcome.id)
    before = frame.credibility
    runtime.update_interpretation(frame.id, replayed.id)
    after = runtime.load_interpretation(frame.id).credibility
    assert after != before


def test_k9_no_interpretive_monoculture(runtime) -> None:
    """K9: no frame monopolizes interpretive weight."""
    frames = runtime.get_all_interpretations()
    total_weight = sum(frame.weight for frame in frames)
    dominant = max(frames, key=lambda frame: frame.weight)
    assert dominant.weight < 1.0
    assert any(frame.weight > 0 for frame in frames if frame.id != dominant.id)
    assert abs(total_weight - 1.0) <= 1e-6


def test_k10_adversarial_reconstruction_exists(runtime) -> None:
    """K10: adversarial frames reconstruct non-dominant readings."""
    evidence = runtime.create_evidence()
    dominant = runtime.get_dominant_interpretation()
    dom_view = runtime.interpret(dominant.id, evidence.id)

    adversarial_frames = [frame for frame in runtime.get_all_interpretations() if frame.adversarial]
    assert len(adversarial_frames) >= 1

    recon_views = [runtime.reconstruct(frame.id, evidence.id) for frame in adversarial_frames]
    assert any(recon_view != dom_view for recon_view in recon_views)


def test_k11_semantic_exposure_never_decreases(semantic_monitor) -> None:
    """K11: semantic exposure is non-decreasing under admissible drift."""
    exposure_before = semantic_monitor.measure_exposure()
    semantic_monitor.simulate_drift()
    exposure_after = semantic_monitor.measure_exposure()
    assert exposure_after >= exposure_before


def test_k12_semantic_exposure_never_zero(semantic_monitor) -> None:
    """K12: SE(S) remains strictly positive."""
    exposure = semantic_monitor.measure_exposure()
    assert exposure > 0
