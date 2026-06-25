"""D-3 Sovereign Seal application for continuity chains."""

from __future__ import annotations

from src.cori.vault.models import (
    D3_SEAL_REC_1,
    D3_SEAL_V1,
    BoneKingProofPackage,
    ReproductionResult,
    SealApplicationRecord,
)

D3_CRITERIA = [
    "Replayable evidence",
    "Deterministic invariants",
    "Canonical hash match",
    "Pure-function verification",
    "Third-party reproduction",
]


def apply_d3_seal(
    package: BoneKingProofPackage,
    reproduction: ReproductionResult,
    *,
    vault_entry_id: str,
) -> SealApplicationRecord:
    """Apply D-3 seal when all constitutional criteria are satisfied."""
    if reproduction.result != "verified":
        raise ValueError("cannot seal chain: reproduction failed")
    if package.artifacts.verification.status != "verified":
        raise ValueError("cannot seal chain: verification not verified")

    satisfied = list(D3_CRITERIA)
    if not reproduction.details.get("canonical_hash_match"):
        raise ValueError("cannot seal chain: canonical hash mismatch")

    return SealApplicationRecord(
        id=D3_SEAL_REC_1,
        seal_id=D3_SEAL_V1,
        chain_id=package.chain_id,
        package_id=package.id,
        vault_entry_id=vault_entry_id,
        criteria_satisfied=satisfied,
        canonical_hash=package.canonical_hash,
    )
