"""Canonical loop hash for runtime mesh audit (re-export)."""

from __future__ import annotations

from uuid import UUID

from src.cori.pel.canonical import compute_hash, compute_loop_hash

__all__ = ["compute_hash", "compute_loop_hash", "compute_loop_hash_legacy"]


def compute_loop_hash_legacy(
    subject_id: UUID,
    asset_id: UUID,
    evidence_id: UUID,
    validation_id: UUID,
    decision: str,
) -> str:
    return compute_loop_hash(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
