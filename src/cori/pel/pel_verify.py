"""Independent PEL verification — recompute canonical hash and compare."""

from __future__ import annotations

import os

from src.cori.pel.canonical import compute_hash
from src.cori.pel.models import Claim, PELRecord, VerificationRecord

VERIFICATION_METHOD = f"pel_verify.py@{os.environ.get('GIT_SHA', 'alpha')}"


def canonical_payload_hash(payload: dict) -> str:
    """Alias for Alpha canonical hashing."""
    return compute_hash(payload)


def verify_pel_record(pel: PELRecord, claim: Claim) -> VerificationRecord:
    """
    Alpha invariant:
    - Recompute the canonical hash from pel.raw
    - Compare to pel.primary_hash
    """
    recomputed = compute_hash(pel.raw)

    if recomputed == pel.primary_hash:
        status = "verified"
        details: dict = {"message": "hash matches"}
    else:
        status = "failed"
        details = {
            "message": "hash mismatch",
            "expected": pel.primary_hash,
            "actual": recomputed,
        }

    return VerificationRecord(
        claim_id=claim.id,
        pel_record_id=pel.id,
        status=status,
        method=VERIFICATION_METHOD,
        details=details,
    )
