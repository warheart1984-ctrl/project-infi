"""Ingest runtime audit records into the Primary Evidence Ledger."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from src.cori.pel.canonical import canonical_loop_payload, compute_loop_hash
from src.cori.pel.models import Claim, PELRecord


def pel_from_loop(
    *,
    audit_id: UUID | str,
    subject_id: UUID,
    asset_id: UUID,
    evidence_id: UUID,
    validation_id: UUID,
    decision: Literal["approved", "rejected", "pending"],
    loop_hash: str | None = None,
    request_body: dict[str, Any] | None = None,
    observed_at: datetime | None = None,
) -> PELRecord:
    """Build a PEL record from a completed core-loop audit."""
    raw = canonical_loop_payload(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
    primary = loop_hash or compute_loop_hash(
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
    )
    observed = observed_at or datetime.now(UTC).replace(microsecond=0)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return PELRecord(
        primary_hash=primary,
        actor_ref=str(subject_id),
        object_ref=str(asset_id),
        evidence_ref=str(evidence_id),
        validation_ref=str(validation_id),
        decision=decision,
        raw=raw,
        audit_id=str(audit_id),
        observed_at=observed,
    )


def default_t1_claim() -> Claim:
    """Standard Tier-1 governance claim for the first verified Alpha loop."""
    return Claim(
        kind="governance",
        summary="CORI Alpha can produce a governed decision with full provenance for a single asset.",
        description=(
            "A real user can complete the CORI Alpha core loop (identity, asset, evidence, "
            "validation, decision, audit), and the resulting audit record can be independently "
            "verified via the PEL and pel_verify.py."
        ),
        status="active",
        tier="T1",
    )
