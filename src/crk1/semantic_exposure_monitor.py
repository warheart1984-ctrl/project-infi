"""CRK-1 Semantic Exposure Monitor — real-time SE(S) tracker (K11–K12)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.crk1.errors import ConstitutionalError

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime


class SemanticExposureMonitor:
    """Tracks SE(S) = αP + βA + γC + δR over the interpretive layer."""

    def __init__(
        self,
        runtime: CRK1Runtime,
        *,
        alpha: float = 1.0,
        beta: float = 1.0,
        gamma: float = 1.0,
        delta: float = 1.0,
    ) -> None:
        if min(alpha, beta, gamma, delta) <= 0:
            raise ValueError("α, β, γ, δ must be > 0")
        self.runtime = runtime
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self._last_exposure: float | None = None
        self._history: list[dict[str, float]] = []

    def snapshot(self) -> dict[str, float]:
        """Record SE(S) and component exposures for drift replay (K11)."""
        parts = self.components()
        exposure = (
            self.alpha * parts["prediction"]
            + self.beta * parts["adversarial"]
            + self.gamma * parts["challenge"]
            + self.delta * parts["reconstruction"]
        )
        record = {"se": exposure, **parts}
        self._history.append(record)
        return record

    @property
    def history(self) -> list[dict[str, float]]:
        return list(self._history)

    def SE(self, snapshot: dict[str, float]) -> float:
        """Semantic exposure at a recorded interpretive snapshot (K12)."""
        return float(snapshot.get("se", 0.0))

    def _prediction_exposure(self) -> float:
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return 0.0
        bound = [frame for frame in frames if frame.prediction_binding]
        return len(bound) / len(frames)

    def _adversarial_exposure(self) -> float:
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return 0.0
        adversarial = [frame for frame in frames if frame.adversarial]
        return len(adversarial) / len(frames)

    def _challenge_exposure(self) -> float:
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return 0.0
        dominant = max(frames, key=lambda frame: frame.weight)
        others = [frame for frame in frames if frame.id != dominant.id]
        if not others:
            return 0.0
        return sum(frame.weight for frame in others)

    def _reconstruction_exposure(self) -> float:
        evidence = self.runtime.get_all_evidence()
        if not evidence:
            return 0.0
        plural = 0
        for item in evidence:
            try:
                if len(self.runtime.get_interpretations(item.id)) >= 2:
                    plural += 1
            except ConstitutionalError:
                continue
        return plural / len(evidence)

    def components(self) -> dict[str, float]:
        return {
            "prediction": self._prediction_exposure(),
            "adversarial": self._adversarial_exposure(),
            "challenge": self._challenge_exposure(),
            "reconstruction": self._reconstruction_exposure(),
        }

    def measure_exposure(self) -> float:
        parts = self.components()
        exposure = (
            self.alpha * parts["prediction"]
            + self.beta * parts["adversarial"]
            + self.gamma * parts["challenge"]
            + self.delta * parts["reconstruction"]
        )
        if exposure <= 0:
            raise ConstitutionalError("K12 violation: semantic exposure must be > 0")
        self._last_exposure = exposure
        return exposure

    def simulate_drift(self) -> None:
        """Apply K11-admissible semantic drift and enforce non-decreasing SE(S)."""
        before = self.snapshot()["se"]
        self.runtime.apply_semantic_drift()
        after = self.snapshot()["se"]
        if after < before - 1e-9:
            raise ConstitutionalError("K11 violation: semantic exposure decreased")
