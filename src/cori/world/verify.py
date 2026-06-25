"""Mechanical verification of world claims by replay."""

from __future__ import annotations

import os

from src.cori.world.models import WorldClaim, WorldEventRecord, WorldVerificationRecord
from src.cori.world.replay import replay_world

VERIFICATION_METHOD = f"verify_world_claim@{os.environ.get('GIT_SHA', 'alpha')}"


def verify_world_claim(
    claim: WorldClaim,
    events: list[WorldEventRecord],
) -> WorldVerificationRecord:
    """
    Alpha world invariant:
    - Replay events into state
    - Check derived condition holds at claim.location
    """
    state = replay_world(events)
    location_data = state.locations.get(claim.location, {})
    flags = location_data.get("flags", {}) if isinstance(location_data, dict) else {}

    if claim.claim_type == "boss_defeated" and flags.get("boss_defeated") is True:
        status = "verified"
        details = {
            "message": "replay confirms boss_defeated flag",
            "location": claim.location,
        }
    else:
        status = "failed"
        details = {
            "message": "replay does not support claim",
            "location": claim.location,
            "flags": flags,
            "claim_type": claim.claim_type,
        }

    return WorldVerificationRecord(
        claim_id=claim.id,
        status=status,
        method=VERIFICATION_METHOD,
        details=details,
    )
