"""CRK-T2 — Constitutional boundary detection (backward-compatible facade)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from src.kernel.amendment_controller import (
    DEFAULT_PERSISTENCE_EPOCHS as DEFAULT_CONSECUTIVE_EPOCHS,
    DEFAULT_THETA_HIGH,
    DEFAULT_THETA_LOW,
    KernelAmendmentController,
)
from src.kernel.boundary_monitor import DEFAULT_ALPHA, DEFAULT_WEIGHTS, KernelBoundaryMonitor
from src.kernel.governance import Governance
from src.kernel.kernel_boundary_loop import KernelBoundaryLoop
from src.kernel.spine_telemetry import (
    SpineBoundaryTelemetry,
    count_contract_failures,
    detect_contract_overlap,
    measure_fitness_drift,
    measure_replay_complexity,
    measure_semantic_overlap,
    telemetry_from_spine,
)

SIGNAL_KEYS = (
    "semantic_duplication",
    "replay_complexity",
    "invariant_violations",
    "fitness_divergence",
    "contract_redundancy",
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True, slots=True)
class BoundaryTelemetry:
    semantic_duplication: float = 0.0
    replay_complexity: float = 0.0
    invariant_violations: float = 0.0
    fitness_divergence: float = 0.0
    contract_redundancy: float = 0.0

    def as_vector(self) -> tuple[float, float, float, float, float]:
        return (
            _clamp(self.semantic_duplication),
            _clamp(self.replay_complexity),
            _clamp(self.invariant_violations),
            _clamp(self.fitness_divergence),
            _clamp(self.contract_redundancy),
        )

    def to_dict(self) -> dict[str, float]:
        return {key: getattr(self, key) for key in SIGNAL_KEYS}


@dataclass(frozen=True, slots=True)
class BoundaryControlConfig:
    weights: tuple[float, float, float, float, float] = tuple(float(w) for w in DEFAULT_WEIGHTS)
    alpha: float = DEFAULT_ALPHA
    theta_high: float = DEFAULT_THETA_HIGH
    theta_low: float = DEFAULT_THETA_LOW
    consecutive_epochs: int = DEFAULT_CONSECUTIVE_EPOCHS

    def __post_init__(self) -> None:
        if not 0.0 < self.alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        if self.theta_low >= self.theta_high:
            raise ValueError("theta_low must be less than theta_high")
        if self.consecutive_epochs < 1:
            raise ValueError("consecutive_epochs must be >= 1")
        total = sum(self.weights)
        if total <= 0:
            raise ValueError("weights must sum to a positive value")
        normalized = tuple(weight / total for weight in self.weights)
        object.__setattr__(self, "weights", normalized)


@dataclass
class OuterLoopState:
    kernel_version: int = 1
    insufficiency_smoothed: float = 0.0
    consecutive_high_epochs: int = 0
    amendment_signal: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "kernel_version": self.kernel_version,
            "insufficiency_smoothed": round(self.insufficiency_smoothed, 6),
            "consecutive_high_epochs": self.consecutive_high_epochs,
            "amendment_signal": self.amendment_signal,
        }


class _StaticTelemetry:
    def __init__(self, telemetry: BoundaryTelemetry) -> None:
        self._telemetry = telemetry

    def semantic_overlap_score(self) -> float:
        return self._telemetry.semantic_duplication

    def replay_depth_score(self) -> float:
        return self._telemetry.replay_complexity

    def contract_violation_rate(self) -> float:
        return self._telemetry.invariant_violations

    def fitness_drift_score(self) -> float:
        return self._telemetry.fitness_divergence

    def contract_overlap_score(self) -> float:
        return self._telemetry.contract_redundancy


class _GovernanceAdapter:
    def __init__(self, *, ratify: bool = False, kernel_version: int = 1) -> None:
        self._ratify = ratify
        self._kernel_version = kernel_version

    def current_kernel_version(self) -> int:
        return self._kernel_version

    def amendment_store(self) -> Any:
        return Governance.current().amendment_store()

    def propose_kernel_amendment(self, **kwargs: Any) -> bool:
        ratify = bool(kwargs.get("ratify")) or self._ratify
        if ratify:
            self._kernel_version += 1
            return True
        return False


def compute_insufficiency(
    telemetry: BoundaryTelemetry,
    config: BoundaryControlConfig,
) -> float:
    monitor = KernelBoundaryMonitor(_StaticTelemetry(telemetry), alpha=config.alpha, weights=list(config.weights))
    signals = monitor.compute_raw_signals()
    return _clamp(float(signals.dot(monitor.weights)))


def smooth_insufficiency(
    raw: float,
    previous_smoothed: float,
    *,
    alpha: float,
) -> float:
    return _clamp(alpha * raw + (1.0 - alpha) * previous_smoothed)


def decide_amendment(
    insufficiency_smoothed: float,
    state: OuterLoopState,
    config: BoundaryControlConfig,
) -> tuple[int, int]:
    controller = KernelAmendmentController(
        theta_high=config.theta_high,
        theta_low=config.theta_low,
        persistence_epochs=config.consecutive_epochs,
    )
    controller.high_count = state.consecutive_high_epochs
    controller.last_u = state.amendment_signal
    u = controller.decide(insufficiency_smoothed)
    return u, controller.high_count


def update_kernel_version(
    kernel_version: int,
    amendment_signal: int,
    ratified: bool,
) -> int:
    if amendment_signal and ratified:
        return kernel_version + 1
    return kernel_version


def step_outer_loop(
    state: OuterLoopState,
    telemetry: BoundaryTelemetry,
    *,
    ratified: bool = False,
    config: BoundaryControlConfig | None = None,
) -> tuple[OuterLoopState, dict[str, Any]]:
    cfg = config or BoundaryControlConfig()
    governance = _GovernanceAdapter(ratify=ratified, kernel_version=state.kernel_version)
    loop = KernelBoundaryLoop(_StaticTelemetry(telemetry), governance)
    loop.monitor.alpha = cfg.alpha
    loop.monitor.weights = np.array(cfg.weights, dtype=float)
    loop.monitor.prev_I = state.insufficiency_smoothed
    loop.controller = KernelAmendmentController(
        theta_high=cfg.theta_high,
        theta_low=cfg.theta_low,
        persistence_epochs=cfg.consecutive_epochs,
    )
    loop.controller.high_count = state.consecutive_high_epochs
    loop.controller.last_u = state.amendment_signal
    loop.kernel_version = state.kernel_version

    report = loop.step(ratify=ratified)
    raw = loop.monitor.compute_raw_signals()
    report["insufficiency_raw"] = round(float(raw.dot(loop.monitor.weights)), 6)
    report["insufficiency_smoothed"] = report["insufficiency"]
    report["ratified"] = ratified
    report["amendment_ratified"] = report["amendment_triggered"]
    report["telemetry"] = telemetry.to_dict()

    next_state = OuterLoopState(
        kernel_version=report["kernel_version"],
        insufficiency_smoothed=report["insufficiency_smoothed"],
        consecutive_high_epochs=report["consecutive_high_epochs"],
        amendment_signal=0 if report["amendment_triggered"] else report["amendment_signal"],
    )
    return next_state, report


@dataclass
class BoundaryController:
    config: BoundaryControlConfig = field(default_factory=BoundaryControlConfig)
    state: OuterLoopState = field(default_factory=OuterLoopState)
    governance: Governance = field(default_factory=Governance.current)

    def __post_init__(self) -> None:
        self._loop = KernelBoundaryLoop(
            SpineBoundaryTelemetry(spine={}),
            self.governance,
            ledger_store=self.governance.amendment_store(),
        )
        self._loop.kernel_version = self.state.kernel_version
        self._loop.monitor.prev_I = self.state.insufficiency_smoothed
        self._loop.controller.high_count = self.state.consecutive_high_epochs
        self._loop.controller.last_u = self.state.amendment_signal
        self._loop.monitor.alpha = self.config.alpha
        self._loop.monitor.weights = np.array(self.config.weights, dtype=float)

    def _sync_state_from_loop(self, report: dict[str, Any]) -> None:
        self.state.kernel_version = report["kernel_version"]
        self.state.insufficiency_smoothed = report["insufficiency"]
        self.state.consecutive_high_epochs = report["consecutive_high_epochs"]
        self.state.amendment_signal = report.get("amendment_signal", 0)

    def observe_spine(self, spine: dict[str, Any], *, ratified: bool = False) -> dict[str, Any]:
        report = self._loop.observe_spine(spine, ratify=ratified)
        raw = self._loop.monitor.compute_raw_signals()
        report["insufficiency_raw"] = round(float(raw.dot(self._loop.monitor.weights)), 6)
        report["insufficiency_smoothed"] = report["insufficiency"]
        report["ratified"] = ratified
        report["amendment_ratified"] = report["amendment_triggered"]
        report["telemetry"] = {
            SIGNAL_KEYS[i]: round(float(raw[i]), 6) for i in range(len(SIGNAL_KEYS))
        }
        self.governance.set_kernel_version(self._loop.kernel_version)
        self._sync_state_from_loop(report)
        report["outer_loop_state"] = self.state.to_dict()
        return report
