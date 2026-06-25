"""Steward isolation proofs for assimilation experiments."""

from __future__ import annotations

from .hashing import sha256_hex


def prove_isolation(steward_id: str, original_participant_ids: list[str]) -> str:
    if steward_id in original_participant_ids:
        raise ValueError(f"{steward_id} is not isolated from original calibration")
    return sha256_hex(
        {
            "steward_id": steward_id,
            "original_participants": sorted(original_participant_ids),
            "isolated": True,
        }
    )
