"""Vault models for Continuity Proof #001 and sovereign seal records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from src.cori.world.models import (
    WorldClaim,
    WorldClaimRecord,
    WorldEventRecord,
    WorldMemoryRecord,
    WorldState,
    WorldVerificationRecord,
)

CHAIN_BK_1 = "CHAIN-BK-1"
VAULT_CP_001 = "VAULT-CP-001"
BK_PKG_1 = "BK-PKG-1"
MISSION_001 = "MISSION-001"
D3_SEAL_V1 = "D3-SEAL-v1"
D3_SEAL_REC_1 = "D3-SEAL-REC-1"
BK_CANONICAL_HASH = "b1d4f5a5c9a5e7d8565617aadd6240213664bd624120ba31dce290fbeba53f52"
CATEGORY_B_CRITERIA: list[tuple[str, str]] = [
    ("B-1", "Independent Execution Environment"),
    ("B-2", "No Founder Assistance"),
    ("B-3", "Replay State Match"),
    ("B-4", "Evidence Extraction Match"),
    ("B-5", "Claim Verification Match"),
    ("B-6", "Canonical Hash Match"),
    ("B-7", "Observer Report Submitted"),
]
REPRODUCTION_PROTOCOL_RP_10 = "RP-1.0"
FIRC_VERSION = "FIRC-1.0"
AVCP_VERSION = "AVCP-1.0"
CTS_VERSION = "CTS-1.0"
OBSERVER_BUNDLE_VERSION = "1.0"


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


class WorldStateSnapshot(BaseModel):
    """Immutable replay state at a point in the continuity chain."""

    id: str
    chain_id: str
    state: WorldState
    captured_at: datetime


class ProofArtifacts(BaseModel):
    event: WorldEventRecord
    memory: WorldMemoryRecord
    replay_state: WorldStateSnapshot
    derived_claim: WorldClaim
    claim_record: WorldClaimRecord
    verification: WorldVerificationRecord


class BoneKingProofPackage(BaseModel):
    id: str = BK_PKG_1
    chain_id: str = CHAIN_BK_1
    designation: str = "CP-001"
    version: str = "1.0"
    mission_id: str = MISSION_001
    artifacts: ProofArtifacts
    canonical_hash: str = ""


class ReproductionLogEntry(BaseModel):
    observer: str
    timestamp: datetime
    result: Literal["verified", "failed"]
    notes: str = ""


class VaultEntry(BaseModel):
    id: str = VAULT_CP_001
    title: str = "Continuity Proof #001 — Bone King"
    classification: Literal["Public", "Restricted"] = "Public"
    version: str = "1.0"
    created_at: datetime = Field(default_factory=_utc_now)
    created_by: str = "Vault"
    mission_id: str = MISSION_001
    chain_id: str = CHAIN_BK_1
    summary: str = "First independently verifiable continuity chain produced by Continuity OS."
    package_id: str = BK_PKG_1
    canonical_hash: str = ""
    reproduction_instructions: str = f"Execute {REPRODUCTION_PROTOCOL_RP_10} using {BK_PKG_1}."
    reproduction_log: list[ReproductionLogEntry] = Field(default_factory=list)
    status: Literal["draft", "verified", "sealed", "completed"] = "draft"


class SealApplicationRecord(BaseModel):
    id: str = D3_SEAL_REC_1
    seal_id: str = D3_SEAL_V1
    chain_id: str = CHAIN_BK_1
    package_id: str = BK_PKG_1
    vault_entry_id: str = VAULT_CP_001
    applied_at: datetime = Field(default_factory=_utc_now)
    applied_by: str = "Vault"
    criteria_satisfied: list[str] = Field(default_factory=list)
    canonical_hash: str = ""
    reproduction_category: Literal["A", "B"] | None = None
    founder_independent: bool = False
    observer_report_hash: str | None = None


class LineageProofRegistration(BaseModel):
    id: str = Field(default_factory=lambda: f"LINEAGE-PROOF-{uuid4()}")
    lineage_root_id: str = "LINEAGE-0001"
    vault_entry_id: str = VAULT_CP_001
    chain_id: str = CHAIN_BK_1
    proof_designation: str = "CP-001"
    registered_at: datetime = Field(default_factory=_utc_now)


class CeremonyAnnouncement(BaseModel):
    ceremony_id: str = AVCP_VERSION
    vault_entry_id: str
    seal_record_id: str
    chain_id: str
    canonical_hash: str
    announced_at: datetime = Field(default_factory=_utc_now)
    message: str = ""


class ReproductionResult(BaseModel):
    protocol: str = REPRODUCTION_PROTOCOL_RP_10
    package_id: str
    observer: str = "Vault"
    result: Literal["verified", "failed"]
    details: dict[str, Any] = Field(default_factory=dict)
    reproduced_at: datetime = Field(default_factory=_utc_now)


class CategoryBCriterion(BaseModel):
    """RP-1.0 / FIRC-1.0 Category B requirement."""

    id: str
    title: str
    satisfied: bool
    notes: str = ""


class ObserverReportRecord(BaseModel):
    """Signed observer report for founder-independent reproduction."""

    id: str = Field(default_factory=lambda: f"OBS-RPT-{uuid4().hex[:8].upper()}")
    observer: str
    mission_id: str = MISSION_001
    package_id: str = BK_PKG_1
    reproduction_category: Literal["B"] = "B"
    environment: dict[str, str] = Field(default_factory=dict)
    canonical_hash_confirmed: str = BK_CANONICAL_HASH
    criteria: list[CategoryBCriterion] = Field(default_factory=list)
    rp_version: str = REPRODUCTION_PROTOCOL_RP_10
    firc_version: str = FIRC_VERSION
    report_hash: str = ""
    submitted_at: datetime = Field(default_factory=_utc_now)


class MissionCompletionRecord(BaseModel):
    """Mission dossier completion after Category B reproduction."""

    id: str = "MISSION-001-COMPLETION"
    mission_id: str = MISSION_001
    status: Literal["COMPLETED"] = "COMPLETED"
    previous_status: Literal["VERIFIED"] = "VERIFIED"
    reproduction_category: Literal["B"] = "B"
    canonical_hash: str = BK_CANONICAL_HASH
    observer: str
    seal_id: str = D3_SEAL_V1
    environment_details: dict[str, str] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=_utc_now)


class CeremonyCompletionRecord(BaseModel):
    """FIRC-1.0 closure ceremony tying observer report to vault artifacts."""

    ceremony_id: str = FIRC_VERSION
    mission_id: str = MISSION_001
    vault_entry_id: str = VAULT_CP_001
    seal_record_id: str = D3_SEAL_REC_1
    observer_report_id: str
    package_id: str = BK_PKG_1
    observer_bundle_version: str = OBSERVER_BUNDLE_VERSION
    rp_compliant: bool = True
    firc_compliant: bool = True
    evidence_bundle_refs: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=_utc_now)


class TrustBoundaryUpdate(BaseModel):
    """CTS lineage update after founder-independent proof."""

    chain_id: str = CHAIN_BK_1
    designation: str = "first founder-independent continuity proof"
    lineage_registered: bool = True
    continuity_ledger_updated: bool = True
    updated_at: datetime = Field(default_factory=_utc_now)


class MissionDossierRecord(BaseModel):
    """Archived mission state after closure."""

    mission_id: str = MISSION_001
    state: Literal["CLOSED"] = "CLOSED"
    archived_artifacts: list[str] = Field(default_factory=list)
    final_proof_bundle: str = BK_PKG_1
    closed_at: datetime = Field(default_factory=_utc_now)


@dataclass
class CategoryBClosureResult:
    package: BoneKingProofPackage
    vault_entry: VaultEntry
    seal_record: SealApplicationRecord
    lineage_registration: LineageProofRegistration
    observer_report: ObserverReportRecord
    mission_completion: MissionCompletionRecord
    ceremony_completion: CeremonyCompletionRecord
    trust_boundary_update: TrustBoundaryUpdate
    mission_dossier: MissionDossierRecord
