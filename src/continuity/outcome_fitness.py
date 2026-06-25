"""Outcome fitness — variance analysis, drift scoring, and spine health (UGR-OUT-1 / PIT-2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

OIT_CAPABILITY_ID = "OIT-1"
OIT_2_CAPABILITY_ID = "OIT-2"


@dataclass(frozen=True, slots=True)
class OutcomeConfig:
    theta_outcome_drift: float = 0.5
    critical_blocks_epoch: bool = True
    window: int = 10


@dataclass(frozen=True, slots=True)
class OutcomeStrip:
    outcome_id: str
    decision_id: str
    epoch: int
    variance_classification: str
    variance_delta: dict[str, float]
    expected_summary: str
    observed_summary: str
    constitutional_role: str = "PIT-2 / RTC-1 reality feedback"

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "epoch": self.epoch,
            "variance_classification": self.variance_classification,
            "variance_delta": dict(self.variance_delta),
            "expected_summary": self.expected_summary,
            "observed_summary": self.observed_summary,
            "constitutional_role": self.constitutional_role,
        }


def _metric_maps(payload: dict[str, Any]) -> dict[str, float]:
    metrics = (payload.get("metrics") or {}) if isinstance(payload, dict) else {}
    result: dict[str, float] = {}
    for key, value in metrics.items():
        try:
            result[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return result


def compute_variance(
    expected: dict[str, Any],
    observed: dict[str, Any],
    *,
    cfg: OutcomeConfig | None = None,
) -> dict[str, Any]:
    _ = cfg
    expected_metrics = _metric_maps(expected)
    observed_metrics = _metric_maps(observed)
    keys = sorted(set(expected_metrics) | set(observed_metrics))
    delta: dict[str, float] = {}
    for key in keys:
        delta[key] = round(observed_metrics.get(key, 0.0) - expected_metrics.get(key, 0.0), 6)
    return {"delta": delta}


def classify_variance(variance: dict[str, Any], *, cfg: OutcomeConfig | None = None) -> str:
    _ = cfg
    deltas = variance.get("delta") or {}
    if not deltas:
        return "acceptable"
    severities: list[float] = []
    for key, raw in deltas.items():
        delta = abs(float(raw))
        if str(key).endswith("_ms") or str(key).endswith("_count"):
            if delta >= 50:
                severities.append(1.0)
            elif delta >= 10:
                severities.append(0.5)
            else:
                severities.append(0.0)
            continue
        if delta >= 0.15:
            severities.append(1.0)
        elif delta >= 0.03:
            severities.append(0.5)
        else:
            severities.append(0.0)
    peak = max(severities) if severities else 0.0
    if peak >= 1.0:
        return "critical"
    if peak >= 0.5:
        return "concerning"
    return "acceptable"


def compute_outcome_drift(outcomes: list[Any], *, window: int = 10) -> float:
    recent = sorted(outcomes, key=lambda item: getattr(item, "epoch", 0), reverse=True)[:window]
    if not recent:
        return 0.0
    scores: list[float] = []
    for outcome in recent:
        variance = outcome.variance if hasattr(outcome, "variance") else outcome.get("variance", {})
        cls = variance.get("classification") if isinstance(variance, dict) else "acceptable"
        if cls == "acceptable":
            scores.append(0.0)
        elif cls == "concerning":
            scores.append(0.5)
        else:
            scores.append(1.0)
    return round(sum(scores) / len(scores), 6)


def build_outcome_strip(record: Any) -> OutcomeStrip:
    expected = record.expected if hasattr(record, "expected") else record.get("expected", {})
    observed = record.observed if hasattr(record, "observed") else record.get("observed", {})
    variance = record.variance if hasattr(record, "variance") else record.get("variance", {})
    return OutcomeStrip(
        outcome_id=str(record.id if hasattr(record, "id") else record.get("id")),
        decision_id=str(record.decision_id if hasattr(record, "decision_id") else record.get("decision_id")),
        epoch=int(record.epoch if hasattr(record, "epoch") else record.get("epoch") or 0),
        variance_classification=str(variance.get("classification") or "acceptable"),
        variance_delta={str(k): float(v) for k, v in (variance.get("delta") or {}).items()},
        expected_summary=str(expected.get("description") or ""),
        observed_summary=str(observed.get("description") or ""),
    )


def build_outcome_health(
    *,
    outcome_store: Any | None = None,
    cfg: OutcomeConfig | None = None,
) -> dict[str, Any]:
    from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger

    config = cfg or OutcomeConfig()
    store = outcome_store or OutcomeLedgerStore(config=config)
    bootstrap_outcome_ledger(store)
    outcomes = store.list_outcomes()
    drift = compute_outcome_drift(outcomes, window=config.window)
    critical = [
        item.id
        for item in outcomes
        if (item.variance or {}).get("classification") == "critical"
    ]
    concerning = [
        item.id
        for item in outcomes
        if (item.variance or {}).get("classification") == "concerning"
    ]
    epoch_blocked = config.critical_blocks_epoch and drift > config.theta_outcome_drift
    objects = [build_outcome_strip(item).to_dict() for item in outcomes[-config.window :]]

    return {
        "outcome_drift": drift,
        "theta_outcome_drift": config.theta_outcome_drift,
        "critical_outcomes": critical,
        "concerning_outcomes": concerning,
        "objects": objects,
        "epoch_commit_blocked": epoch_blocked,
        "warnings": [
            {"code": "OIT-CRITICAL", "outcome_id": outcome_id} for outcome_id in critical
        ]
        + [
            {"code": "OIT-CONCERNING", "outcome_id": outcome_id} for outcome_id in concerning
        ],
        "canonical": "UGR-OUT-1 — OutcomeObject reality feedback",
    }
