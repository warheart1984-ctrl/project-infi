"""Stewardability forecast model — quantitative continuity phase prediction."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.stewardability.lineage_event_log import LineageEventLog
from src.cos1.accumulation.ae_json_schema import AccumulationEventLog
from src.cos1.accumulation.chain_detector import (
    ClassifiedAccumulationEvent,
    detect_compounding_chains,
)

ForecastPhase = Literal["EARLY", "EMERGENT", "COMPOUNDING", "NEAR_STEWARDABILITY"]


class LineageMetrics(BaseModel):
    propagation: int = 0
    convergence: int = 0
    accumulation: int = 0
    avg_chain_length: float = 0.0
    cross_domain_spread: int = 0


class StewardabilityForecast(BaseModel):
    probability: float = Field(ge=0.0, le=1.0)
    phase: ForecastPhase = "EARLY"
    metrics: LineageMetrics = Field(default_factory=LineageMetrics)


def compute_lineage_metrics(
    lineage_log: LineageEventLog,
    accumulation_log: AccumulationEventLog,
) -> LineageMetrics:
    propagation = len(lineage_log.propagation_events())
    convergence = len(lineage_log.convergence_events())
    accumulation = len(accumulation_log.accumulation_events())

    classified = [
        ClassifiedAccumulationEvent.from_accumulation_event(event)
        for event in accumulation_log.events
    ]
    chains = detect_compounding_chains(classified)
    avg_chain = (
        sum(chain.length for chain in chains) / len(chains) if chains else 0.0
    )

    domains: set[str] = set()
    for event in lineage_log.events:
        domains.add(event.actor.domain)
    for event in accumulation_log.events:
        domains.add(event.actor.domain)

    return LineageMetrics(
        propagation=propagation,
        convergence=convergence,
        accumulation=accumulation,
        avg_chain_length=avg_chain,
        cross_domain_spread=len(domains),
    )


def forecast_stewardability(metrics: LineageMetrics) -> StewardabilityForecast:
    """
    Weighted logistic-style score → tanh squash → phase bands.

    Propagation → vitality; convergence → reality-tracking;
    accumulation → continuity; chain length → generational depth;
    cross-domain spread → universality.
    """
    score = (
        0.2 * math.log1p(metrics.propagation)
        + 0.3 * math.log1p(metrics.convergence)
        + 0.4 * math.log1p(metrics.accumulation)
        + 0.3 * metrics.avg_chain_length
        + 0.2 * math.log1p(metrics.cross_domain_spread)
    )
    probability = math.tanh(score / 4)

    phase: ForecastPhase = "EARLY"
    if probability > 0.25:
        phase = "EMERGENT"
    if probability > 0.5:
        phase = "COMPOUNDING"
    if probability > 0.75:
        phase = "NEAR_STEWARDABILITY"

    return StewardabilityForecast(
        probability=probability,
        phase=phase,
        metrics=metrics,
    )


def forecast_from_logs(
    lineage_log: LineageEventLog,
    accumulation_log: AccumulationEventLog,
) -> StewardabilityForecast:
    metrics = compute_lineage_metrics(lineage_log, accumulation_log)
    return forecast_stewardability(metrics)
