"""FCRM-1 — Founder-Capture Risk Model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.stewardability.drift_detector import DriftSignal
from src.continuity.stewardability.register import StewardAbilityRegister
from src.continuity.css.spec import (
    FCRM1_FORMULA,
    FCRM_ALPHA_REJECTION,
    FCRM_BETA_BOTTLENECK,
    FCRM_DELTA_SUPPRESSION,
    FCRM_GAMMA_DOGMATISM,
    FCRM_HIGH_RISK_THRESHOLD,
)

FCRM1_REFERENCE = "Founder-Capture Risk Model FCRM-1"


class FounderCaptureSignals(BaseModel):
    rejection_of_extensions: float = 0.0
    governance_bottleneck: float = 0.0
    dogmatism: float = 0.0
    successor_suppression: float = 0.0


class FCRM1Assessment(BaseModel):
    reference: str = FCRM1_REFERENCE
    formula: str = FCRM1_FORMULA
    signals: FounderCaptureSignals = Field(default_factory=FounderCaptureSignals)
    risk_score: float = 0.0
    high_risk: bool = False
    continuity_failure_likely: bool = False
    indicators: list[str] = Field(default_factory=list)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def assess_fcrm1(
    register: StewardAbilityRegister,
    drift_signals: list[DriftSignal] | None = None,
    *,
    rejection_events: int = 0,
    suppression_events: int = 0,
) -> FCRM1Assessment:
    """
    FCR = αR + βB + γD + δS

    Derives signals from stewardability register blockages and drift detector.
    """
    drift_signals = drift_signals or []
    blockages = register.blockage_events()
    demonstrations = register.demonstration_events()

    rejection = _clamp(
        rejection_events / 3.0
        + len([event for event in blockages if "reject" in (event.notes or "").lower()]) * 0.25
    )
    bottleneck = _clamp(
        len([signal for signal in drift_signals if signal.kind == "GATEKEEPING"]) * 0.35
        + len(blockages) * 0.15
    )
    dogmatism = _clamp(
        len([signal for signal in drift_signals if signal.kind == "IMITATION"]) * 0.2
        + len([event for event in blockages if "dogma" in (event.notes or "").lower()]) * 0.4
    )
    suppression = _clamp(
        suppression_events / 2.0
        + len([event for event in blockages if "suppress" in (event.notes or "").lower()]) * 0.35
        + max(0, len(demonstrations) - len(register.emergence_events())) * 0.1
    )

    signals = FounderCaptureSignals(
        rejection_of_extensions=rejection,
        governance_bottleneck=bottleneck,
        dogmatism=dogmatism,
        successor_suppression=suppression,
    )

    risk = (
        FCRM_ALPHA_REJECTION * rejection
        + FCRM_BETA_BOTTLENECK * bottleneck
        + FCRM_GAMMA_DOGMATISM * dogmatism
        + FCRM_DELTA_SUPPRESSION * suppression
    )
    risk = round(_clamp(risk), 4)
    high = risk >= FCRM_HIGH_RISK_THRESHOLD

    indicators: list[str] = []
    if rejection > 0.3:
        indicators.append("Founders rejecting lineage-compatible extensions.")
    if bottleneck > 0.3:
        indicators.append("Governance bottlenecking detected.")
    if dogmatism > 0.3:
        indicators.append("Identity treated as dogma rather than grammar.")
    if suppression > 0.3:
        indicators.append("Successor contributions suppressed.")

    return FCRM1Assessment(
        signals=signals,
        risk_score=risk,
        high_risk=high,
        continuity_failure_likely=high,
        indicators=indicators,
    )
