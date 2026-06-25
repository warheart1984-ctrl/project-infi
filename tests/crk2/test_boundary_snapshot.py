"""Boundary snapshot (read-only) vs step tests."""

from __future__ import annotations

import numpy as np

from src.kernel.amendment_controller import KernelAmendmentController
from src.kernel.boundary_monitor import KernelBoundaryMonitor
from src.kernel.governance import Governance
from src.kernel.kernel_boundary_loop import KernelBoundaryLoop


class _OnesTelemetry:
    def semantic_overlap_score(self) -> float:
        return 1.0

    def replay_depth_score(self) -> float:
        return 1.0

    def contract_violation_rate(self) -> float:
        return 1.0

    def fitness_drift_score(self) -> float:
        return 1.0

    def contract_overlap_score(self) -> float:
        return 1.0


def test_snapshot_does_not_advance_controller_streak() -> None:
    Governance.reset()
    loop = KernelBoundaryLoop(_OnesTelemetry(), Governance.current())
    loop.controller = KernelAmendmentController(theta_high=0.45, theta_low=0.1, persistence_epochs=3)
    loop.monitor.alpha = 1.0

    first = loop.snapshot()
    second = loop.snapshot()

    assert first["consecutive_high_epochs"] == second["consecutive_high_epochs"] == 0
    assert first["insufficiency"] == second["insufficiency"]


def test_step_advances_ema_and_persistence() -> None:
    Governance.reset()
    loop = KernelBoundaryLoop(_OnesTelemetry(), Governance.current())
    loop.controller = KernelAmendmentController(theta_high=0.45, theta_low=0.1, persistence_epochs=3)
    loop.monitor.alpha = 1.0

    loop.step()
    loop.step()
    report = loop.step()

    assert report["consecutive_high_epochs"] >= 1
    assert report["insufficiency"] >= 0.45
