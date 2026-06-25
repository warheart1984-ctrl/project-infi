"""Dashboard API for Alpha evidence cycles (PEL + Claim + Verification)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.cori.pel.models import Claim, PELRecord, VerificationRecord
from src.cori.pel.storage import ClaimStorage, PelStorage, VerificationStorage

router = APIRouter(prefix="/dashboard", tags=["evidence-dashboard"])


class EvidenceCycleView(BaseModel):
    pel: PELRecord
    claim: Claim
    verification: VerificationRecord


@router.get("/evidence-cycles", response_model=list[EvidenceCycleView])
def list_evidence_cycles() -> list[EvidenceCycleView]:
    pel_storage = PelStorage()
    claim_storage = ClaimStorage()
    verif_storage = VerificationStorage()

    views: list[EvidenceCycleView] = []
    for verification in verif_storage.list_all():
        try:
            pel = pel_storage.get_by_id(verification.pel_record_id)
            claim = claim_storage.get_by_id(verification.claim_id)
        except KeyError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        views.append(EvidenceCycleView(pel=pel, claim=claim, verification=verification))
    return views
