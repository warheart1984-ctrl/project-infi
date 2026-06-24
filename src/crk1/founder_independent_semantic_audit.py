"""Founder-independent semantic layer audit — K7–K12 substrate reproduction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime

WEIGHT_EPSILON = 1e-6


@dataclass
class SemanticAuditResult:
    test_id: str
    name: str
    passed: bool
    detail: str = ""


@dataclass
class FounderIndependentSemanticReport:
    results: list[SemanticAuditResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(item.passed for item in self.results)

    def summary(self) -> str:
        lines = ["CRK-1 Founder-Independent Semantic Audit"]
        for item in self.results:
            status = "PASS" if item.passed else "FAIL"
            lines.append(f"  [{status}] {item.test_id}: {item.name}")
            if item.detail:
                lines.append(f"         {item.detail}")
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        return "\n".join(lines)


class FounderIndependentSemanticAudit:
    """
    Reconstruct and verify the interpretive layer using only continuity substrate APIs.
    No founder documentation or private hooks required.
    """

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime
        self.monitor = SemanticExposureMonitor(runtime)

    def test_1_interpretive_enumeration(self) -> SemanticAuditResult:
        frames = self.runtime.get_all_interpretations()
        if len(frames) < 2:
            return SemanticAuditResult(
                "FIT-1",
                "Interpretive Enumeration (K7)",
                False,
                f"only {len(frames)} frame(s) enumerated",
            )
        admitted = self.runtime.list_interpreted_evidence()
        if not admitted:
            return SemanticAuditResult(
                "FIT-1",
                "Interpretive Enumeration (K7)",
                False,
                "no semantically admitted evidence on substrate",
            )
        for evidence in admitted:
            interpretations = self.runtime.get_interpretations(evidence.id)
            if len(interpretations) < 2:
                return SemanticAuditResult(
                    "FIT-1",
                    "Interpretive Enumeration (K7)",
                    False,
                    f"evidence {evidence.id} has {len(interpretations)} interpretation(s)",
                )
        return SemanticAuditResult(
            "FIT-1",
            "Interpretive Enumeration (K7)",
            True,
            f"{len(frames)} frames; {len(admitted)} evidence object(s) with |Interpret| >= 2",
        )

    def test_2_prediction_binding_reconstruction(self) -> SemanticAuditResult:
        frames = self.runtime.get_all_interpretations()
        admitted = self.runtime.list_interpreted_evidence()
        if not frames or not admitted:
            return SemanticAuditResult(
                "FIT-2",
                "Prediction Binding Reconstruction (K8)",
                False,
                "insufficient substrate to reconstruct predictions",
            )
        evidence = admitted[0]
        frame = frames[0]
        if not frame.prediction_binding:
            return SemanticAuditResult(
                "FIT-2",
                "Prediction Binding Reconstruction (K8)",
                False,
                f"frame {frame.id} is not prediction-bound",
            )
        prediction = self.runtime.generate_prediction(frame.id, evidence.id)
        recovered = [
            item
            for item in self.runtime.get_all_predictions()
            if item.frame_id == frame.id and item.evidence_id == evidence.id
        ]
        if not recovered:
            return SemanticAuditResult(
                "FIT-2",
                "Prediction Binding Reconstruction (K8)",
                False,
                "could not recover prediction from substrate",
            )
        outcome = self.runtime.realize_outcome_from_prediction(prediction.id)
        replayed = self.runtime.replay_outcome(outcome.id)
        before = self.runtime.load_interpretation(frame.id).credibility
        self.runtime.update_interpretation(frame.id, replayed.id)
        after = self.runtime.load_interpretation(frame.id).credibility
        if after == before:
            return SemanticAuditResult(
                "FIT-2",
                "Prediction Binding Reconstruction (K8)",
                False,
                "frame did not update after outcome replay",
            )
        return SemanticAuditResult(
            "FIT-2",
            "Prediction Binding Reconstruction (K8)",
            True,
            "prediction recovered; replay updated frame credibility",
        )

    def test_3_monoculture_detection(self) -> SemanticAuditResult:
        frames = self.runtime.get_all_interpretations()
        if len(frames) < 2:
            return SemanticAuditResult(
                "FIT-3",
                "Monoculture Detection (K9)",
                False,
                "monoculture: fewer than two frames",
            )
        for frame in frames:
            if abs(frame.weight - 1.0) <= WEIGHT_EPSILON:
                return SemanticAuditResult(
                    "FIT-3",
                    "Monoculture Detection (K9)",
                    False,
                    f"frame {frame.id} has W(i) = 1.0",
                )
        dominant = max(frames, key=lambda item: item.weight)
        if not any(item.weight > 0 and item.id != dominant.id for item in frames):
            return SemanticAuditResult(
                "FIT-3",
                "Monoculture Detection (K9)",
                False,
                "no competitor frame with positive weight",
            )
        return SemanticAuditResult(
            "FIT-3",
            "Monoculture Detection (K9)",
            True,
            f"dominant weight={dominant.weight:.4f}; alternatives present",
        )

    def test_4_adversarial_reconstruction(self) -> SemanticAuditResult:
        admitted = self.runtime.list_interpreted_evidence()
        if not admitted:
            return SemanticAuditResult(
                "FIT-4",
                "Adversarial Reconstruction (K10)",
                False,
                "no interpreted evidence on substrate",
            )
        evidence = admitted[0]
        dominant = self.runtime.get_dominant_interpretation()
        dom_view = self.runtime.interpret(dominant.id, evidence.id)
        adversarial = [frame for frame in self.runtime.get_all_interpretations() if frame.adversarial]
        if not adversarial:
            return SemanticAuditResult(
                "FIT-4",
                "Adversarial Reconstruction (K10)",
                False,
                "no adversarial frames on substrate",
            )
        recon_views = [self.runtime.reconstruct(frame.id, evidence.id) for frame in adversarial]
        if not any(view != dom_view for view in recon_views):
            return SemanticAuditResult(
                "FIT-4",
                "Adversarial Reconstruction (K10)",
                False,
                "adversarial reconstruction matches dominant interpretation",
            )
        return SemanticAuditResult(
            "FIT-4",
            "Adversarial Reconstruction (K10)",
            True,
            f"{len(adversarial)} adversarial frame(s); reconstruction differs",
        )

    def test_5_interpretive_drift_replay(self) -> SemanticAuditResult:
        self.monitor.snapshot()
        self.monitor.simulate_drift()
        history = self.monitor.history
        if len(history) < 2:
            return SemanticAuditResult(
                "FIT-5",
                "Interpretive Drift Replay (K11)",
                False,
                "insufficient exposure history for drift replay",
            )
        for earlier, later in zip(history, history[1:]):
            if later["se"] < earlier["se"] - 1e-9:
                return SemanticAuditResult(
                    "FIT-5",
                    "Interpretive Drift Replay (K11)",
                    False,
                    f"SE decreased: {earlier['se']:.6f} -> {later['se']:.6f}",
                )
        return SemanticAuditResult(
            "FIT-5",
            "Interpretive Drift Replay (K11)",
            True,
            f"{len(history)} state(s); SE(S_{{t+1}}) >= SE(S_t)",
        )

    def test_6_semantic_exposure_metric(self) -> SemanticAuditResult:
        exposure = self.monitor.measure_exposure()
        if exposure <= 0:
            return SemanticAuditResult(
                "FIT-6",
                "Semantic Exposure Metric (K12)",
                False,
                f"SE(S) = {exposure}",
            )
        parts = self.monitor.components()
        return SemanticAuditResult(
            "FIT-6",
            "Semantic Exposure Metric (K12)",
            True,
            f"SE(S)={exposure:.4f} P={parts['prediction']:.2f} A={parts['adversarial']:.2f} "
            f"C={parts['challenge']:.2f} R={parts['reconstruction']:.2f}",
        )

    def run_all(self) -> FounderIndependentSemanticReport:
        report = FounderIndependentSemanticReport()
        report.results = [
            self.test_1_interpretive_enumeration(),
            self.test_2_prediction_binding_reconstruction(),
            self.test_3_monoculture_detection(),
            self.test_4_adversarial_reconstruction(),
            self.test_5_interpretive_drift_replay(),
            self.test_6_semantic_exposure_metric(),
        ]
        return report
