"""O / I / I₂ / V epistemic modes — Python parity with cos1-accumulation-sim."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.ra.jpss_accumulation_sim import JPSSContributionEvent

EpistemicMode = Literal["OBSERVATION", "INTERPRETATION", "INTEGRATION", "VALIDATION"]
AccumulationOrigin = Literal["PLA", "LA", "SA"]
EpistemicBehaviorProfile = Literal["doctrine", "framework", "instrument", "nascent"]


class EpistemicMetrics(BaseModel):
    observation_count: int = 0
    interpretation_count: int = 0
    integration_count: int = 0
    validation_count: int = 0
    obs_to_interp_ratio: float = 0.0
    interp_to_validation_ratio: float = 0.0
    external_observation_count: int = 0
    profile: EpistemicBehaviorProfile = "nascent"


def classify_mode(
    event: JPSSContributionEvent,
    *,
    explicit_mode: EpistemicMode | None = None,
) -> EpistemicMode:
    """Classify epistemic mode when not explicitly set."""
    if explicit_mode:
        return explicit_mode
    if event.mode:
        return event.mode  # type: ignore[return-value]
    if event.accumulation_type == "NONE" and not event.from_exposure:
        return "OBSERVATION"
    if event.governance_behavior == "validate":
        return "VALIDATION"
    if event.governance_behavior == "integrate":
        return "INTEGRATION"
    return "INTERPRETATION"


def classify_origin(event: JPSSContributionEvent) -> AccumulationOrigin:
    if event.origin:
        return event.origin  # type: ignore[return-value]
    if not event.from_exposure and event.accumulation_type == "NONE":
        return "PLA"
    if event.from_exposure:
        return "LA"
    return "SA"


def tag_contribution_event(
    event: JPSSContributionEvent,
    *,
    mode: EpistemicMode | None = None,
    origin: AccumulationOrigin | None = None,
) -> JPSSContributionEvent:
    """Apply origin + mode tags at ingestion (parity with TS withEventTags)."""
    tagged = event.model_copy(
        update={
            "mode": mode or classify_mode(event),
            "origin": origin or classify_origin(event),
        }
    )
    return tagged


def compute_epistemic_metrics(events: list[JPSSContributionEvent]) -> EpistemicMetrics:
    """Compute O/I/I₂/V counts and doctrine vs instrument profile."""
    obs = [event for event in events if event.mode == "OBSERVATION"]
    interp = [event for event in events if event.mode == "INTERPRETATION"]
    integ = [event for event in events if event.mode == "INTEGRATION"]
    valid = [event for event in events if event.mode == "VALIDATION"]

    o_count = len(obs)
    i_count = len(interp)
    i2_count = len(integ)
    v_count = len(valid)

    obs_to_interp = o_count / i_count if i_count else 0.0
    interp_to_valid = i_count / v_count if v_count else 0.0
    external_obs = len([event for event in obs if not event.from_exposure])

    profile = _resolve_profile(o_count, i_count, v_count, obs_to_interp)

    return EpistemicMetrics(
        observation_count=o_count,
        interpretation_count=i_count,
        integration_count=i2_count,
        validation_count=v_count,
        obs_to_interp_ratio=obs_to_interp,
        interp_to_validation_ratio=interp_to_valid,
        external_observation_count=external_obs,
        profile=profile,
    )


def _resolve_profile(
    o_count: int,
    i_count: int,
    v_count: int,
    obs_to_interp: float,
) -> EpistemicBehaviorProfile:
    """Classify JPSS as doctrine, framework, or instrument from epistemic balance."""
    if o_count == 0 and i_count > 0:
        return "doctrine"
    if v_count == 0 and i_count > o_count:
        return "framework"
    if o_count >= 2 and v_count >= 1 and obs_to_interp >= 0.5:
        return "instrument"
    return "nascent"
