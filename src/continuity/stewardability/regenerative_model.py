"""Regenerative Continuity Model (RCM-1) — stewardability enables stack regeneration."""

from __future__ import annotations

from pydantic import BaseModel

from src.continuity.stewardability.operating_conditions import (
    StewardabilityConditions,
    is_stewardability_viable,
)
from src.continuity.stewardability.register import StewardAbilityRegister


class ContinuityState(BaseModel):
    artifacts_intact: bool = True
    stewards_present: bool = False
    stewardability_viable: bool = False


def next_continuity_state(
    current: ContinuityState,
    conditions: StewardabilityConditions,
    register: StewardAbilityRegister,
) -> ContinuityState:
    viable = is_stewardability_viable(conditions)
    has_stewards = bool(register.emergence_events())

    return ContinuityState(
        artifacts_intact=current.artifacts_intact,
        stewards_present=has_stewards,
        stewardability_viable=viable,
    )


def continuity_succeeded(state: ContinuityState) -> bool:
    """Deep criterion: stewardability + stewards trump artifact survival alone."""
    if state.stewardability_viable and state.stewards_present:
        return True
    return False
