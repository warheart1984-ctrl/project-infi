"""Stewardability Drift Detector — erosion of capacity to generate stewards."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.stewardability.register import StewardAbilityRegister, StewardabilityEvent

DriftKind = Literal[
    "EMERGENCE_DRIFT",
    "GATEKEEPING_DRIFT",
    "IMITATION_DRIFT",
    "ENVIRONMENT_DRIFT",
    "TEST_DRIFT",
]

DriftSeverity = Literal["LOW", "MEDIUM", "HIGH"]

DEFAULT_EMERGENCE_GAP_DAYS = 365
MIN_RECONSTRUCTIONS_FOR_DEMO = 3


class DriftSignal(BaseModel):
    kind: DriftKind
    severity: DriftSeverity
    evidence: list[StewardabilityEvent] = Field(default_factory=list)
    explanation: str


def _is_long_gap(events: list[StewardabilityEvent], gap_days: int) -> bool:
    if not events:
        return True
    latest = max(event.timestamp for event in events)
    return datetime.now(UTC) - latest > timedelta(days=gap_days)


def _only_agreement(demonstrations: list[StewardabilityEvent]) -> bool:
    if not demonstrations:
        return False
    for event in demonstrations:
        demo = event.demonstration
        if demo is None:
            continue
        if demo.critiques:
            return False
        if demo.lineage_impact != "UNCHANGED":
            return False
    return True


def _gatekeeping_ratio(register: StewardAbilityRegister) -> float:
    blockages = len(register.blockage_events())
    attempts = blockages + len(register.emergence_events())
    if attempts == 0:
        return 0.0
    return blockages / attempts


def detect_stewardability_drift(
    register: StewardAbilityRegister,
    *,
    emergence_gap_days: int = DEFAULT_EMERGENCE_GAP_DAYS,
    gatekeeping_threshold: float = 0.8,
) -> list[DriftSignal]:
    """Detect when steward generation capacity is eroding, ossifying, or captured."""
    signals: list[DriftSignal] = []

    emergence_events = register.emergence_events()
    demonstration_events = register.demonstration_events()

    if not emergence_events or _is_long_gap(emergence_events, emergence_gap_days):
        signals.append(
            DriftSignal(
                kind="EMERGENCE_DRIFT",
                severity="HIGH",
                evidence=emergence_events,
                explanation="No new stewards have emerged over a significant period.",
            )
        )

    if _only_agreement(demonstration_events):
        signals.append(
            DriftSignal(
                kind="IMITATION_DRIFT",
                severity="MEDIUM",
                evidence=demonstration_events,
                explanation=(
                    "Stewardship demonstrations show agreement only; "
                    "principled disagreement is absent."
                ),
            )
        )

    ratio = _gatekeeping_ratio(register)
    if register.blockage_events() and ratio >= gatekeeping_threshold:
        signals.append(
            DriftSignal(
                kind="GATEKEEPING_DRIFT",
                severity="HIGH",
                evidence=register.blockage_events(),
                explanation=(
                    f"Recognition appears captured by incumbents "
                    f"({ratio:.0%} of attempts blocked)."
                ),
            )
        )

    weak_demos = [
        event
        for event in demonstration_events
        if event.demonstration is not None
        and len(event.demonstration.reconstructions) < MIN_RECONSTRUCTIONS_FOR_DEMO
    ]
    if demonstration_events and len(weak_demos) == len(demonstration_events):
        signals.append(
            DriftSignal(
                kind="TEST_DRIFT",
                severity="MEDIUM",
                evidence=weak_demos,
                explanation=(
                    "Succession demonstrations are shallow — "
                    "insufficient reconstruction across continuity layers."
                ),
            )
        )

    low_novelty = [
        event
        for event in register.events
        if not event.context.novelty_profile
        or event.context.novelty_profile == ["UNSPECIFIED"]
    ]
    if register.events and len(low_novelty) == len(register.events):
        signals.append(
            DriftSignal(
                kind="ENVIRONMENT_DRIFT",
                severity="MEDIUM",
                evidence=low_novelty[:5],
                explanation="No environments with real novelty/conflict to test stewardship.",
            )
        )

    return signals
