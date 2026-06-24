"""CRK-1 semantic replay engine tests."""

from __future__ import annotations

from src.crk1.interpretive_lineage_tree import InterpretiveLineageTree
from src.crk1.semantic_drift_auditor import SemanticDriftAuditor
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor
from src.crk1.semantic_replay_engine import SemanticReplayEngine


def test_semantic_replay_views(runtime) -> None:
    engine = SemanticReplayEngine(runtime)
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    runtime.generate_prediction(frame.id, evidence.id)

    bundle = engine.replay_semantic_state(evidence.id)
    assert bundle["views"]["evidence_id"] == evidence.id
    assert len(bundle["views"]["interpretations"]) >= 2
    assert bundle["predictions"][0]["expected_outcome"]
    assert len(bundle["reconstructions"]) >= 1
    assert bundle["reconstructions"][0]["divergence_from_dominant"] > 0


def test_prediction_realization_replay(runtime) -> None:
    engine = SemanticReplayEngine(runtime)
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    prediction = runtime.generate_prediction(frame.id, evidence.id)

    pending = engine.replay_predictions(evidence.id)
    assert pending[0]["realized_outcome"] == "pending"

    runtime.realize_outcome_from_prediction(prediction.id)
    realized = engine.replay_predictions(evidence.id)
    assert realized[0]["realized_outcome"] == "realized"


def test_interpretive_lineage_tree(runtime) -> None:
    tree = InterpretiveLineageTree(runtime)
    tree.assert_lineage_integrity()

    dominant = runtime.get_dominant_interpretation()
    adversarial = next(frame for frame in runtime.get_all_interpretations() if frame.adversarial)

    assert dominant.lineage == []
    assert dominant.id in adversarial.lineage
    assert dominant.id in tree.get_ancestors(adversarial.id)
    assert adversarial.id in tree.get_descendants(dominant.id)


def test_semantic_drift_auditor_passes(semantic_monitor) -> None:
    auditor = SemanticDriftAuditor(semantic_monitor.runtime, semantic_monitor)
    assert auditor.audit() is True
