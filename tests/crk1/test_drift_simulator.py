"""CRK-1 drift simulator tests."""

from __future__ import annotations

from src.crk1.drift_simulator import DriftSimulator
from src.crk1.runtime_facade import CRK1Runtime
from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


def _warm_runtime(crk1_runtime) -> CRK1Runtime:
    facade = CRK1Runtime(crk1_runtime)
    root = crk1_runtime.ledgers.identity.id
    facade.propose_and_execute(identity=root, evidence=["EVD-CRK1-001"])
    facade.create_evidence()
    return facade


def test_drift_simulator_admissible_mutation(crk1_runtime) -> None:
    facade = _warm_runtime(crk1_runtime)
    sim = DriftSimulator(facade, semantic_monitor=SemanticExposureMonitor(facade))
    result = sim.test_drift(
        {"target": "constitution", "changes": {"governance.quorum": 3}},
    )
    assert result["CE_preserved"] is True
    assert result["constitutional"] is True


def test_drift_simulator_rejects_insulating_mutation(crk1_runtime) -> None:
    facade = _warm_runtime(crk1_runtime)
    sim = DriftSimulator(facade, semantic_monitor=SemanticExposureMonitor(facade))
    result = sim.test_drift(
        {"target": "constitution", "changes": {"Outcome.replayable": False}},
    )
    assert result["constitutional"] is False
    assert result.get("error") == "mutation_rejected"


def test_drift_simulator_interpretation_mutation(crk1_runtime) -> None:
    facade = _warm_runtime(crk1_runtime)
    sim = DriftSimulator(facade, semantic_monitor=SemanticExposureMonitor(facade))
    before = sim.measure()
    result = sim.test_drift({"target": "interpretation", "changes": {}})
    assert result["SE_preserved"] is True
    assert result["after"]["SE"] >= before["SE"] - 1e-9


def test_drift_simulator_batch(crk1_runtime) -> None:
    facade = _warm_runtime(crk1_runtime)
    sim = DriftSimulator(facade, semantic_monitor=SemanticExposureMonitor(facade))
    results = sim.test_mutation_set(
        [
            {"target": "governance", "changes": {"governance.quorum": 4}},
            {"target": "constitution", "changes": {"Outcome.replayable": False}},
        ]
    )
    assert len(results) == 2
    assert results[0]["constitutional"] is True
    assert results[1]["constitutional"] is False
