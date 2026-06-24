"""CRK-1 Semantic Drift Auditor — detect interpretive capture attempts (K9–K12)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.crk1.errors import ConstitutionalError

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime
    from src.crk1.semantic_exposure_monitor import SemanticExposureMonitor


class SemanticDriftAuditor:
    """Runs monoculture, adversarial-loss, and SE(S) exposure checks."""

    def __init__(self, runtime: CRK1Runtime, semantic_monitor: SemanticExposureMonitor) -> None:
        self.runtime = runtime
        self.monitor = semantic_monitor

    def check_monoculture(self) -> bool:
        """K9 — no frame may achieve structural dominance."""
        frames = self.runtime.get_all_interpretations()
        if not frames:
            return False

        dominant = max(frames, key=lambda frame: frame.weight)
        if dominant.weight >= 1.0:
            raise ConstitutionalError("Semantic drift: interpretive monoculture detected")

        return True

    def check_adversarial_loss(self) -> bool:
        """K10 — at least one adversarial frame must remain."""
        frames = self.runtime.get_all_interpretations()
        adversarial = [frame for frame in frames if frame.adversarial]
        if not adversarial:
            raise ConstitutionalError("Semantic drift: no adversarial frames remain")
        return True

    def check_exposure(self) -> bool:
        """K11/K12 — SE(S) must remain strictly positive."""
        exposure = self.monitor.measure_exposure()
        if exposure <= 0:
            raise ConstitutionalError("Semantic drift: SE(S) ≤ 0 (semantic insulation)")
        return True

    def audit(self) -> bool:
        """Run all semantic drift checks; raise ConstitutionalError on failure."""
        self.check_monoculture()
        self.check_adversarial_loss()
        self.check_exposure()
        return True
