"""Auto-derive claims from replayed world state."""

from __future__ import annotations

from src.cori.world.models import WorldClaim, WorldClaimRecord, WorldEventRecord, WorldState


def derive_world_claims(state: WorldState) -> list[WorldClaim]:
    claims: list[WorldClaim] = []
    for location, data in state.locations.items():
        flags = data.get("flags", {})
        if not isinstance(flags, dict):
            continue
        if flags.get("boss_defeated") is True:
            claims.append(
                WorldClaim(
                    summary=f"The boss in {location} was defeated.",
                    claim_type="boss_defeated",
                    location=location,
                )
            )
    return claims


def generate_world_claim_record(
    claim: WorldClaim,
    events: list[WorldEventRecord],
) -> WorldClaimRecord:
    """Link a derived claim to the minimal supporting event evidence."""
    event_ids = [event.id for event in events]
    return WorldClaimRecord(
        claim_id=claim.id,
        event_ids=event_ids,
        raw={
            "claim_id": claim.id,
            "claim_type": claim.claim_type,
            "location": claim.location,
            "event_ids": event_ids,
        },
    )
