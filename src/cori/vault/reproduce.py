"""RP-1.0 — deterministic third-party reproduction of a continuity package."""

from __future__ import annotations

from src.cori.vault.canonical import compute_package_hash
from src.cori.vault.models import (
    REPRODUCTION_PROTOCOL_RP_10,
    BoneKingProofPackage,
    ReproductionLogEntry,
    ReproductionResult,
)
from src.cori.world.replay import replay_world
from src.cori.world.verify import verify_world_claim


def reproduce_package(
    package: BoneKingProofPackage,
    *,
    observer: str = "Observer-01",
) -> ReproductionResult:
    """
    RP-1.0: replay events, recompute invariants, confirm canonical hash stability.
    """
    artifacts = package.artifacts
    events = [artifacts.event]
    state = replay_world(events)
    verification = verify_world_claim(artifacts.derived_claim, events)

    recomputed_hash = compute_package_hash(artifacts)
    hash_match = recomputed_hash == package.canonical_hash
    state_match = state.model_dump() == artifacts.replay_state.state.model_dump()
    boss_flag = (
        state.locations.get(artifacts.derived_claim.location, {})
        .get("flags", {})
        .get("boss_defeated")
        is True
    )

    verified = (
        verification.status == "verified"
        and hash_match
        and state_match
        and boss_flag
    )

    return ReproductionResult(
        protocol=REPRODUCTION_PROTOCOL_RP_10,
        package_id=package.id,
        observer=observer,
        result="verified" if verified else "failed",
        details={
            "verification_status": verification.status,
            "canonical_hash_match": hash_match,
            "recomputed_hash": recomputed_hash,
            "state_match": state_match,
            "boss_defeated_flag": boss_flag,
        },
    )


def reproduction_log_entry(result: ReproductionResult) -> ReproductionLogEntry:
    notes = "All hashes and artifacts reproduced exactly." if result.result == "verified" else str(
        result.details
    )
    return ReproductionLogEntry(
        observer=result.observer,
        timestamp=result.reproduced_at,
        result=result.result,
        notes=notes,
    )
