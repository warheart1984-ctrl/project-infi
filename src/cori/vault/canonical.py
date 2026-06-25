"""Canonical hashing for continuity proof packages."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.cori.pel.canonical import compute_hash
from src.cori.vault.models import BoneKingProofPackage, ProofArtifacts
from src.cori.world.canonical import compute_event_hash


def _state_canonical(state: dict[str, Any]) -> dict[str, Any]:
    return state


def canonical_package_payload(artifacts: ProofArtifacts) -> dict[str, Any]:
    """Deterministic payload for package-level sovereign hash."""
    event = artifacts.event
    memory = artifacts.memory
    claim = artifacts.derived_claim
    verification = artifacts.verification
    return {
        "event_id": event.id,
        "event_hash": memory.event_hash or compute_event_hash(event),
        "replay_state": artifacts.replay_state.state.model_dump(mode="json"),
        "claim_id": claim.id,
        "claim_type": claim.claim_type,
        "claim_location": claim.location,
        "claim_summary": claim.summary,
        "verification_status": verification.status,
        "verification_method": verification.method,
    }


def compute_package_hash(artifacts: ProofArtifacts) -> str:
    return compute_hash(canonical_package_payload(artifacts))


def attach_package_hash(package: BoneKingProofPackage) -> BoneKingProofPackage:
    canonical_hash = compute_package_hash(package.artifacts)
    return package.model_copy(update={"canonical_hash": canonical_hash})
