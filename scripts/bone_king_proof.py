"""Run the minimal Bone King world proof end-to-end."""

from __future__ import annotations

from src.cori.world.claims import derive_world_claims, generate_world_claim_record
from src.cori.world.demo import bone_king_defeated_event
from src.cori.world.register import register_world_event
from src.cori.world.replay import replay_world
from src.cori.world.verify import verify_world_claim


def run_bone_king_proof() -> str:
    """
    Event → Memory → Replay → Claim → Evidence → Verification → Fact

    Returns the verified fact summary string.
    """
    event = bone_king_defeated_event()
    memory = register_world_event(event)
    state = replay_world([event])

    assert state.locations["Forgotten Crypt"]["flags"]["boss_defeated"] is True

    claims = derive_world_claims(state)
    if not claims:
        raise RuntimeError("no claims derived from replayed state")
    claim = claims[0]

    record = generate_world_claim_record(claim, [event])
    verification = verify_world_claim(claim, [event])

    if verification.status != "verified":
        raise RuntimeError(f"verification failed: {verification.details}")

    # Evidence chain integrity checks (no authority, only replay)
    assert memory.event_id == event.id
    assert event.id in record.event_ids
    assert record.claim_id == claim.id
    assert verification.claim_id == claim.id

    return claim.summary


def main() -> int:
    fact = run_bone_king_proof()
    print(f'VERIFIED FACT: "{fact}"')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
