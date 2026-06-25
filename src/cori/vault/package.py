"""Build the Bone King continuity proof package (BK-PKG-1)."""

from __future__ import annotations

from datetime import UTC, datetime

from src.cori.vault.canonical import attach_package_hash
from src.cori.vault.models import (
    BK_PKG_1,
    CHAIN_BK_1,
    BoneKingProofPackage,
    ProofArtifacts,
    WorldStateSnapshot,
)
from src.cori.world.claims import derive_world_claims, generate_world_claim_record
from src.cori.world.demo import bone_king_defeated_event
from src.cori.world.models import WorldClaim, WorldClaimRecord, WorldMemoryRecord, WorldVerificationRecord
from src.cori.world.register import register_world_event
from src.cori.world.replay import replay_world
from src.cori.world.verify import verify_world_claim

_CP001_CAPTURED_AT = datetime(2026, 6, 22, 20, 0, 1, tzinfo=UTC)
_WMR_1 = "WMR-1"
_WCLAIM_1 = "WCLAIM-1"
_WCR_1 = "WCR-1"
_WVERIF_1 = "WVERIF-1"
_SNAPSHOT_1 = "WSS-1"


def build_bone_king_proof_package() -> BoneKingProofPackage:
    """Construct CP-001 package with stable artifact IDs for reproduction."""
    event = bone_king_defeated_event()
    memory = register_world_event(event)
    memory = WorldMemoryRecord(
        id=_WMR_1,
        event_id=memory.event_id,
        event_hash=memory.event_hash,
        raw=memory.raw,
        observed_at=_CP001_CAPTURED_AT,
    )

    state = replay_world([event])
    snapshot = WorldStateSnapshot(
        id=_SNAPSHOT_1,
        chain_id=CHAIN_BK_1,
        state=state,
        captured_at=_CP001_CAPTURED_AT,
    )

    claims = derive_world_claims(state)
    if not claims:
        raise RuntimeError("no claims derived from Bone King replay")
    derived = WorldClaim(
        id=_WCLAIM_1,
        summary=claims[0].summary,
        claim_type=claims[0].claim_type,
        location=claims[0].location,
    )

    claim_record = WorldClaimRecord(
        id=_WCR_1,
        claim_id=derived.id,
        event_ids=[event.id],
        raw=generate_world_claim_record(derived, [event]).raw,
    )

    verification = verify_world_claim(derived, [event])
    verification = WorldVerificationRecord(
        id=_WVERIF_1,
        claim_id=verification.claim_id,
        status=verification.status,
        method=verification.method,
        details=verification.details,
        verified_at=_CP001_CAPTURED_AT,
    )

    if verification.status != "verified":
        raise RuntimeError(f"Bone King package verification failed: {verification.details}")

    artifacts = ProofArtifacts(
        event=event,
        memory=memory,
        replay_state=snapshot,
        derived_claim=derived,
        claim_record=claim_record,
        verification=verification,
    )

    package = BoneKingProofPackage(
        id=BK_PKG_1,
        chain_id=CHAIN_BK_1,
        artifacts=artifacts,
    )
    return attach_package_hash(package)
