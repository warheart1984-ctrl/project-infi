"""PSDD-1 — Post-Surpassment Drift Detector."""

from __future__ import annotations

from pydantic import BaseModel

from src.continuity.ra.models import ConsequenceSample, DriftSignals, PSDClassification
from src.continuity.ra.spec import (
    PSD_CRITICAL_MAX,
    PSD_REEVALUATION_THRESHOLD,
    PSD_REJECTION_THRESHOLD,
    PSD_STABLE_MAX,
    PSD_WATCH_MAX,
    PSD_WEIGHT_CONVERGENCE,
    PSD_WEIGHT_EXPLANATORY,
    PSD_WEIGHT_LOAD,
    PSD_WEIGHT_OPERATIONAL,
    PSD_WEIGHT_PREDICTIVE,
    PSDD1_FORMULA,
    PSDD1_REFERENCE,
)


class PSDD1Assessment(BaseModel):
    reference: str = PSDD1_REFERENCE
    formula: str = PSDD1_FORMULA
    signals: DriftSignals
    flagged_for_reevaluation: bool = False
    rejected: bool = False
    recommended_action: str


def _avg_metric(samples: list[ConsequenceSample], metric: str) -> float | None:
    values = [sample.value for sample in samples if sample.metric == metric]
    if not values:
        return None
    return sum(values) / len(values)


def _divergence_from_baseline(sample_avg: float | None, baseline: float) -> float:
    if sample_avg is None:
        return 0.0
    return max(0.0, baseline - sample_avg)


def _excess_over_baseline(sample_avg: float | None, baseline: float) -> float:
    if sample_avg is None:
        return 0.0
    return max(0.0, sample_avg - baseline)


def classify_psd(aggregate: float) -> PSDClassification:
    if aggregate < PSD_STABLE_MAX:
        return "STABLE"
    if aggregate < PSD_WATCH_MAX:
        return "WATCH"
    if aggregate < PSD_CRITICAL_MAX:
        return "CRITICAL_REVIEW"
    return "ROLLBACK"


def recommended_action_for_psd(classification: PSDClassification) -> str:
    mapping = {
        "STABLE": "Continue monitoring; no action required.",
        "WATCH": "Elevated drift — increase monitoring frequency.",
        "CRITICAL_REVIEW": "Critical drift — schedule steward review.",
        "ROLLBACK": "High post-surpassment drift — rollback or revise.",
    }
    return mapping[classification]


def compute_drift_signals(
    samples: list[ConsequenceSample],
    baseline: float = 0.5,
) -> DriftSignals:
    predictive_divergence = _divergence_from_baseline(
        _avg_metric(samples, "predictiveAccuracy"), baseline
    )
    explanatory_inflation = _excess_over_baseline(_avg_metric(samples, "patchCount"), baseline)
    convergence_failure = _divergence_from_baseline(
        _avg_metric(samples, "crossDomainConvergence"), baseline
    )
    operational_underperformance = _divergence_from_baseline(
        _avg_metric(samples, "operationalOutcome"), baseline
    )
    load_spike = _excess_over_baseline(_avg_metric(samples, "stewardLoad"), baseline)

    aggregate = (
        PSD_WEIGHT_PREDICTIVE * predictive_divergence
        + PSD_WEIGHT_EXPLANATORY * explanatory_inflation
        + PSD_WEIGHT_CONVERGENCE * convergence_failure
        + PSD_WEIGHT_OPERATIONAL * operational_underperformance
        + PSD_WEIGHT_LOAD * load_spike
    )
    classification = classify_psd(aggregate)

    return DriftSignals(
        predictive_divergence=predictive_divergence,
        explanatory_inflation=explanatory_inflation,
        convergence_failure=convergence_failure,
        operational_underperformance=operational_underperformance,
        load_spike=load_spike,
        aggregate_psd=round(aggregate, 4),
        classification=classification,
    )


def assess_psdd1(
    samples: list[ConsequenceSample],
    baseline: float = 0.5,
) -> PSDD1Assessment:
    signals = compute_drift_signals(samples, baseline)
    aggregate = signals.aggregate_psd
    return PSDD1Assessment(
        signals=signals,
        flagged_for_reevaluation=aggregate >= PSD_REEVALUATION_THRESHOLD,
        rejected=aggregate >= PSD_REJECTION_THRESHOLD,
        recommended_action=recommended_action_for_psd(signals.classification),
    )
