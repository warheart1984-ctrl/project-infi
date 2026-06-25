"""Canonical loop payload and hash (Alpha invariant)."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from uuid import UUID


def canonical_loop_payload(
    *,
    subject_id: UUID | str,
    asset_id: UUID | str,
    evidence_id: UUID | str,
    validation_id: UUID | str,
    decision: str,
) -> dict[str, str]:
    """Minimal canonical JSON used for primary_hash / loop_hash."""
    return {
        "subject_id": str(subject_id),
        "asset_id": str(asset_id),
        "evidence_id": str(evidence_id),
        "validation_id": str(validation_id),
        "decision": decision,
    }


def compute_hash(canonical: dict[str, Any]) -> str:
    """SHA-256 of sorted compact JSON (no default=str — canonical must be JSON-native)."""
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_loop_hash(
    *,
    subject_id: UUID | str,
    asset_id: UUID | str,
    evidence_id: UUID | str,
    validation_id: UUID | str,
    decision: str,
) -> str:
    return compute_hash(
        canonical_loop_payload(
            subject_id=subject_id,
            asset_id=asset_id,
            evidence_id=evidence_id,
            validation_id=validation_id,
            decision=decision,
        )
    )
