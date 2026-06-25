"""Alpha end-to-end chain: runtime audit → PEL → claim → verification."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from src.cori.pel.ingest import default_t1_claim, pel_from_loop
from src.cori.pel.models import Claim, PELRecord, VerificationRecord
from src.cori.pel.pel_verify import verify_pel_record


def run_alpha_verification_cycle(
    *,
    audit_id: UUID,
    subject_id: UUID,
    asset_id: UUID,
    evidence_id: UUID,
    validation_id: UUID,
    decision: Literal["approved", "rejected", "pending"],
    loop_hash: str,
    request_body: dict[str, Any] | None = None,
    claim: Claim | None = None,
) -> tuple[PELRecord, Claim, VerificationRecord]:
    """
    Execute the first independently verifiable governance cycle:

    Runtime (core loop) → AuditRecord → PELRecord → Claim → VerificationRecord
    """
    pel = pel_from_loop(
        audit_id=audit_id,
        subject_id=subject_id,
        asset_id=asset_id,
        evidence_id=evidence_id,
        validation_id=validation_id,
        decision=decision,
        loop_hash=loop_hash,
        request_body=request_body,
    )
    governance_claim = claim or default_t1_claim()
    verification = verify_pel_record(pel, governance_claim)
    return pel, governance_claim, verification
