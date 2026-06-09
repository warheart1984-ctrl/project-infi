"""Detect proven contributions and govern auto-reward persistence."""

from __future__ import annotations

import os
from typing import Any

from src.ugr.discovery.standing import (
    EpistemicState,
    Standing,
    epistemic_from_receipt,
    standing_from_receipt,
)

UGR_REWARDS_PROVEN_PERSIST_ENV = "UGR_REWARDS_PROVEN_PERSIST"


def is_standing_proven(receipt: dict[str, Any]) -> bool:
    """True when receipt standing is Proven (3) or higher."""
    return standing_from_receipt(receipt) >= Standing.PROVEN


def is_proven_contribution(receipt: dict[str, Any]) -> bool:
    """True when a discovery receipt qualifies for proven-tier rewards and force_persist."""
    if epistemic_from_receipt(receipt) == EpistemicState.REJECTED:
        return False
    return is_standing_proven(receipt)


def proven_rewards_persist_enabled() -> bool:
    """When true, proven discoveries write reputation even if global shadow-only is on."""
    raw = os.getenv(UGR_REWARDS_PROVEN_PERSIST_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}
