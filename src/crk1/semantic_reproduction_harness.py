"""CRK-1 Reproduction Harness — founder-independent semantic layer verification (K7–K12)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime
    from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


class SemanticReproductionHarness:
    """
    Automated founder-independent reproduction test for the semantic layer.

    Proves the interpretive substrate can be reconstructed without founder knowledge.
    """

    def __init__(self, runtime: CRK1Runtime, semantic_monitor: SemanticExposureMonitor) -> None:
        self.runtime = runtime
        self.monitor = semantic_monitor
        self.runtime.attach_semantic_monitor(semantic_monitor)

    def test_pluralism(self) -> bool:
        admitted = self.runtime.list_interpreted_evidence()
        if not admitted:
            return False
        for evidence in admitted:
            if len(self.runtime.get_interpretations(evidence.id)) < 2:
                return False
        return True

    def test_prediction_binding(self) -> bool:
        for frame in self.runtime.get_all_interpretations():
            if not frame.prediction_binding:
                return False
        return True

    def test_monoculture(self) -> bool:
        frames = self.runtime.get_all_interpretations()
        if len(frames) < 2:
            return False
        dominant = max(frames, key=lambda frame: frame.weight)
        if dominant.weight == 1.0:
            return False
        return True

    def test_adversarial_reconstruction(self) -> bool:
        adversaries = [frame for frame in self.runtime.get_all_interpretations() if frame.adversarial]
        if not adversaries:
            return False
        admitted = self.runtime.list_interpreted_evidence()
        if not admitted:
            return False
        evidence = admitted[-1]
        dominant = self.runtime.get_dominant_interpretation()
        dom_view = self.runtime.interpret(dominant.id, evidence.id)
        if all(self.runtime.reconstruct(frame.id, evidence.id) == dom_view for frame in adversaries):
            return False
        return True

    def test_drift_envelope(self) -> bool:
        history = self.runtime.get_interpretive_history()
        if len(history) < 2:
            return False
        for index in range(len(history) - 1):
            if self.monitor.SE(history[index + 1]) < self.monitor.SE(history[index]):
                return False
        return True

    def test_semantic_exposure(self) -> bool:
        return self.monitor.measure_exposure() > 0

    def run(self) -> dict[str, Any]:
        results = {
            "K7_pluralism": self.test_pluralism(),
            "K8_prediction_binding": self.test_prediction_binding(),
            "K9_anti_monoculture": self.test_monoculture(),
            "K10_adversarial_reconstruction": self.test_adversarial_reconstruction(),
            "K11_drift_envelope": self.test_drift_envelope(),
            "K12_semantic_exposure": self.test_semantic_exposure(),
        }
        results["founder_independent_reproduction"] = all(results.values())
        return results
