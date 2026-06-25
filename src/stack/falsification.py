"""FM1–FM4 falsification metrics — when JPSS fails as an instrument."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.ra.jpss_accumulation_sim import JPSSContributionEvent
from src.stack.epistemic import EpistemicMetrics, compute_epistemic_metrics

FalsificationChannel = Literal[
    "F1_no_observational_improvement",
    "F2_no_convergence",
    "F3_high_interpretation_drift",
    "F4_pla_validation_failure",
]


class FalsificationMetricResult(BaseModel):
    metric_id: str
    value: float
    threshold: float
    instrument_hypothesis_weakens: bool
    explanation: str


class FalsificationAssessment(BaseModel):
    """Four falsification channels + composite instrument verdict."""

    fm1: FalsificationMetricResult
    fm2: FalsificationMetricResult
    fm3: FalsificationMetricResult
    fm4: FalsificationMetricResult
    channels_triggered: list[FalsificationChannel] = Field(default_factory=list)
    instrument_hypothesis_holds: bool = True
    classification: Literal["instrument", "framework", "doctrine", "nascent"] = "nascent"
    epistemic: EpistemicMetrics


def compute_fm1_observation_delta(
    *,
    jps_trained_observation_score: float,
    control_observation_score: float,
) -> FalsificationMetricResult:
    """
    FM1 — Observation Improvement Delta.

    Compare JPSS-trained vs control observers on blind continuity-failure tasks.
    If ΔO ≤ 0 → instrument hypothesis weakens (F1).
    """
    delta = jps_trained_observation_score - control_observation_score
    weakens = delta <= 0
    return FalsificationMetricResult(
        metric_id="FM1",
        value=delta,
        threshold=0.0,
        instrument_hypothesis_weakens=weakens,
        explanation=(
            f"ΔO={delta:.2f}: JPSS-trained observers "
            + ("do not outperform controls (F1)." if weakens else "outperform controls.")
        ),
    )


def compute_fm2_convergence_index(
    events: list[JPSSContributionEvent],
    *,
    min_convergence: float = 0.5,
) -> FalsificationMetricResult:
    """
    FM2 — Observation Convergence Index.

    How often independent observers identify the same structures.
    Low convergence → F2.
    """
    obs = [event for event in events if event.mode == "OBSERVATION"]
    if len(obs) < 2:
        return FalsificationMetricResult(
            metric_id="FM2",
            value=0.0,
            threshold=min_convergence,
            instrument_hypothesis_weakens=True,
            explanation="Insufficient observation events for convergence (F2).",
        )

    anchors: dict[str, int] = {}
    for event in obs:
        key = (event.phenomenon_anchor or event.source_text[:80]).strip().lower()
        anchors[key] = anchors.get(key, 0) + 1

    max_cluster = max(anchors.values()) if anchors else 0
    index = max_cluster / len(obs)
    weakens = index < min_convergence

    return FalsificationMetricResult(
        metric_id="FM2",
        value=index,
        threshold=min_convergence,
        instrument_hypothesis_weakens=weakens,
        explanation=(
            f"Convergence index={index:.2f} "
            + ("below threshold (F2)." if weakens else "meets threshold.")
        ),
    )


def compute_fm3_interpretation_drift_index(
    epistemic: EpistemicMetrics,
    *,
    max_drift_ratio: float = 2.0,
) -> FalsificationMetricResult:
    """
    FM3 — Interpretation Drift Index.

    drift = interpretationCount / observationCount
    If drift grows faster than observation → doctrine behavior (F3).
    """
    o = max(epistemic.observation_count, 1)
    drift = epistemic.interpretation_count / o
    weakens = drift > max_drift_ratio and epistemic.observation_count < epistemic.interpretation_count

    return FalsificationMetricResult(
        metric_id="FM3",
        value=drift,
        threshold=max_drift_ratio,
        instrument_hypothesis_weakens=weakens,
        explanation=(
            f"I/O ratio={drift:.2f} "
            + ("— interpretation outpacing observation (F3)." if weakens else "— balanced.")
        ),
    )


def compute_fm4_pla_validation_failure_rate(
    events: list[JPSSContributionEvent],
    *,
    vas_failures: dict[str, bool] | None = None,
    max_failure_rate: float = 0.5,
) -> FalsificationMetricResult:
    """
    FM4 — PLA Validation Failure Rate.

    PLA interpretations that fail VAS-1 / reality validation.
    High failure rate → F4 (critique, not phenomenon).
    """
    pla = [event for event in events if event.origin == "PLA"]
    if not pla:
        return FalsificationMetricResult(
            metric_id="FM4",
            value=0.0,
            threshold=max_failure_rate,
            instrument_hypothesis_weakens=False,
            explanation="No PLA events to assess.",
        )

    failures = vas_failures or {}
    failed = sum(1 for event in pla if failures.get(event.id, False))
    rate = failed / len(pla) if pla else 0.0
    weakens = rate > max_failure_rate

    return FalsificationMetricResult(
        metric_id="FM4",
        value=rate,
        threshold=max_failure_rate,
        instrument_hypothesis_weakens=weakens,
        explanation=(
            f"PLA VAS-1 failure rate={rate:.2%} "
            + ("exceeds threshold (F4)." if weakens else "within bounds.")
        ),
    )


def assess_falsification(
    events: list[JPSSContributionEvent],
    *,
    jps_trained_observation_score: float = 0.0,
    control_observation_score: float = 0.0,
    vas_failures: dict[str, bool] | None = None,
) -> FalsificationAssessment:
    """Run all four falsification metrics and derive instrument classification."""
    epistemic = compute_epistemic_metrics(events)
    fm1 = compute_fm1_observation_delta(
        jps_trained_observation_score=jps_trained_observation_score,
        control_observation_score=control_observation_score,
    )
    fm2 = compute_fm2_convergence_index(events)
    fm3 = compute_fm3_interpretation_drift_index(epistemic)
    fm4 = compute_fm4_pla_validation_failure_rate(events, vas_failures=vas_failures)

    channels: list[FalsificationChannel] = []
    if fm1.instrument_hypothesis_weakens:
        channels.append("F1_no_observational_improvement")
    if fm2.instrument_hypothesis_weakens:
        channels.append("F2_no_convergence")
    if fm3.instrument_hypothesis_weakens:
        channels.append("F3_high_interpretation_drift")
    if fm4.instrument_hypothesis_weakens:
        channels.append("F4_pla_validation_failure")

    holds = len(channels) == 0
    classification = epistemic.profile if holds else (
        "doctrine" if "F3_high_interpretation_drift" in channels else "framework"
    )

    return FalsificationAssessment(
        fm1=fm1,
        fm2=fm2,
        fm3=fm3,
        fm4=fm4,
        channels_triggered=channels,
        instrument_hypothesis_holds=holds,
        classification=classification,
        epistemic=epistemic,
    )
