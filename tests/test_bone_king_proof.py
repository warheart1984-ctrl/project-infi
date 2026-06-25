"""Tests for the Bone King minimal world proof."""

from __future__ import annotations

from src.cori.world.claims import derive_world_claims, generate_world_claim_record
from src.cori.world.demo import bone_king_defeated_event
from src.cori.world.register import register_world_event
from src.cori.world.replay import replay_world
from src.cori.world.verify import verify_world_claim


def test_replay_sets_boss_defeated_flag() -> None:
    event = bone_king_defeated_event()
    state = replay_world([event])
    assert state.locations["Forgotten Crypt"]["flags"]["boss_defeated"] is True


def test_world_register_hashes_event() -> None:
    event = bone_king_defeated_event()
    memory = register_world_event(event)
    assert memory.event_id == "EVT-1"
    assert len(memory.event_hash) == 64
    assert memory.raw["action_type"] == "boss_defeated"


def test_bone_king_end_to_end() -> None:
    event = bone_king_defeated_event()
    register_world_event(event)
    state = replay_world([event])
    claims = derive_world_claims(state)
    assert len(claims) == 1
    assert claims[0].claim_type == "boss_defeated"
    assert "Forgotten Crypt" in claims[0].summary

    record = generate_world_claim_record(claims[0], [event])
    verification = verify_world_claim(claims[0], [event])
    assert verification.status == "verified"
    assert record.event_ids == ["EVT-1"]


def test_verify_fails_without_matching_event() -> None:
    event = bone_king_defeated_event()
    state = replay_world([])
    claims = derive_world_claims(state)
    assert claims == []

    from src.cori.world.models import WorldClaim

    orphan = WorldClaim(
        summary="The boss in Forgotten Crypt was defeated.",
        claim_type="boss_defeated",
        location="Forgotten Crypt",
    )
    verification = verify_world_claim(orphan, [])
    assert verification.status == "failed"
