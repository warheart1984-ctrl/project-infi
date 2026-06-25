"""Bootstrap governance claims for Alpha evidence cycles."""

from __future__ import annotations

from src.cori.pel.ingest import default_t1_claim
from src.cori.pel.models import Claim


def create_alpha_t1_claim() -> Claim:
    """Canonical Tier-1 governance claim for the first verified Alpha loop."""
    return default_t1_claim()
