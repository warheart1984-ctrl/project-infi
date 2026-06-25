"""CRK-T2 insufficiency monitor — raw signals and EMA-smoothed I_bar(t)."""

from __future__ import annotations

import numpy as np

from src.kernel.spine_telemetry import BoundaryTelemetrySource

DEFAULT_WEIGHTS = np.array([0.25, 0.20, 0.30, 0.15, 0.10], dtype=float)
DEFAULT_ALPHA = 0.35


class KernelBoundaryMonitor:
    """Computes s(t), I(t), and smoothed insufficiency I_bar(t)."""

    def __init__(
        self,
        telemetry: BoundaryTelemetrySource,
        *,
        alpha: float = DEFAULT_ALPHA,
        weights: np.ndarray | list[float] | None = None,
    ) -> None:
        self.telemetry = telemetry
        self.alpha = alpha
        self.prev_I = 0.0
        raw_weights = np.array(weights if weights is not None else DEFAULT_WEIGHTS, dtype=float)
        total = float(raw_weights.sum())
        if total <= 0:
            raise ValueError("weights must sum to a positive value")
        self.weights = raw_weights / total

    def compute_raw_signals(self) -> np.ndarray:
        return np.array(
            [
                self.telemetry.semantic_overlap_score(),
                self.telemetry.replay_depth_score(),
                self.telemetry.contract_violation_rate(),
                self.telemetry.fitness_drift_score(),
                self.telemetry.contract_overlap_score(),
            ],
            dtype=float,
        )

    def peek_insufficiency(self) -> tuple[float, float, np.ndarray]:
        """Read-only insufficiency — does not advance EMA state."""
        signals = np.clip(self.compute_raw_signals(), 0.0, 1.0)
        raw = float(np.dot(self.weights, signals))
        smoothed = float(np.clip(self.alpha * raw + (1.0 - self.alpha) * self.prev_I, 0.0, 1.0))
        return smoothed, raw, signals

    def compute_insufficiency(self) -> tuple[float, np.ndarray]:
        smoothed, _raw, signals = self.peek_insufficiency()
        self.prev_I = smoothed
        return smoothed, signals
