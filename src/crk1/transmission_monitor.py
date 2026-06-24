"""CFT-F3 transmission monitor — evaluate consequence-to-evidence integrity per generation."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

ContinuityBand = Literal["healthy", "degraded", "critical"]


class ConsequenceSummary(BaseModel):
    """Aggregated consequence vector k_g."""

    vector: list[float] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class MacroEvidence(BaseModel):
    """Evidence E_{g+1} produced by transmission operator T(k_g)."""

    vector: list[float] = Field(default_factory=list)
    sourceChannels: list[str] = Field(default_factory=list)


class TransmissionThresholds(BaseModel):
    ok: float = 0.4
    critical: float = 0.1
    consecutiveCriticalLimit: int = 3


class RuntimeFlags(BaseModel):
    allowArchitectureChange: bool = True
    requireChannelExpansion: bool = False
    externalReview: bool = False
    constitutionalFreeze: bool = False


class TransmissionMonitorRecord(BaseModel):
    generation: int
    consequenceSummary: ConsequenceSummary
    macroEvidence: MacroEvidence
    transmissionIntegrity: float
    band: ContinuityBand
    thresholds: TransmissionThresholds
    runtimeFlags: RuntimeFlags


def correlation_proxy(left: list[float], right: list[float]) -> float:
    """Normalized Pearson correlation as a mutual-information proxy."""
    if not left or not right:
        return 0.0

    n = min(len(left), len(right))
    if n < 2:
        return 1.0 if left[:n] == right[:n] else 0.0

    k = left[:n]
    e = right[:n]
    mean_k = sum(k) / n
    mean_e = sum(e) / n
    covariance = sum((ki - mean_k) * (ei - mean_e) for ki, ei in zip(k, e, strict=True))
    var_k = sum((ki - mean_k) ** 2 for ki in k)
    var_e = sum((ei - mean_e) ** 2 for ei in e)
    if var_k == 0.0 or var_e == 0.0:
        return 0.0

    pearson = covariance / math.sqrt(var_k * var_e)
    return max(0.0, min(1.0, pearson))


def classify_band(t_int: float, thresholds: TransmissionThresholds) -> ContinuityBand:
    if t_int >= thresholds.ok:
        return "healthy"
    if t_int > thresholds.critical:
        return "degraded"
    return "critical"


def runtime_flags_for_band(
    band: ContinuityBand,
    *,
    constitutional_freeze: bool = False,
) -> RuntimeFlags:
    return RuntimeFlags(
        allowArchitectureChange=band != "critical",
        requireChannelExpansion=band == "degraded",
        externalReview=band == "critical",
        constitutionalFreeze=constitutional_freeze,
    )


class TransmissionMonitor:
    """Stateful evaluator for F3 transmission integrity across generations."""

    def __init__(self) -> None:
        self._critical_counter = 0

    @property
    def critical_counter(self) -> int:
        return self._critical_counter

    def reset_critical_counter(self) -> None:
        self._critical_counter = 0

    def evaluate_transmission(
        self,
        generation: int,
        k_g: ConsequenceSummary,
        e_next: MacroEvidence,
        thresholds: TransmissionThresholds,
    ) -> TransmissionMonitorRecord:
        t_int = correlation_proxy(k_g.vector, e_next.vector)
        band = classify_band(t_int, thresholds)

        constitutional_freeze = False
        if band == "critical":
            self._critical_counter += 1
            if self._critical_counter >= thresholds.consecutiveCriticalLimit:
                constitutional_freeze = True
        else:
            self._critical_counter = 0

        flags = runtime_flags_for_band(band, constitutional_freeze=constitutional_freeze)

        return TransmissionMonitorRecord(
            generation=generation,
            consequenceSummary=k_g,
            macroEvidence=e_next,
            transmissionIntegrity=t_int,
            band=band,
            thresholds=thresholds,
            runtimeFlags=flags,
        )


def evaluate_transmission(
    generation: int,
    k_g: ConsequenceSummary,
    e_next: MacroEvidence,
    thresholds: TransmissionThresholds,
    *,
    monitor: TransmissionMonitor | None = None,
) -> TransmissionMonitorRecord:
    """Evaluate one generation; optional monitor tracks consecutive critical bands."""
    evaluator = monitor or TransmissionMonitor()
    return evaluator.evaluate_transmission(generation, k_g, e_next, thresholds)
