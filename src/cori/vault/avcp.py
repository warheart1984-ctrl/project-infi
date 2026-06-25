"""AVCP-1.0 — Alpha Verification Ceremony Protocol."""

from __future__ import annotations

from dataclasses import dataclass

from src.cori.vault.cts import enforce_package_boundaries, handle_boundary_violation
from src.cori.vault.models import (
    AVCP_VERSION,
    VAULT_CP_001,
    BoneKingProofPackage,
    CeremonyAnnouncement,
    LineageProofRegistration,
    ReproductionLogEntry,
    SealApplicationRecord,
    VaultEntry,
)
from src.cori.vault.package import build_bone_king_proof_package
from src.cori.vault.reproduce import reproduction_log_entry, reproduce_package
from src.cori.vault.seal import apply_d3_seal


@dataclass
class CeremonyResult:
    package: BoneKingProofPackage
    vault_entry: VaultEntry
    seal_record: SealApplicationRecord
    lineage_registration: LineageProofRegistration
    announcement: CeremonyAnnouncement
    reproduction_log: list[ReproductionLogEntry]


def _ceremony_preconditions(package: BoneKingProofPackage) -> None:
    if not package.canonical_hash:
        raise ValueError("AVCP precondition failed: package missing canonical_hash")
    if package.artifacts.verification.status != "verified":
        raise ValueError("AVCP precondition failed: VerificationRecord not verified")


def register_continuity_proof_in_lineage(
    vault_entry: VaultEntry,
    *,
    lineage_root_id: str = "LINEAGE-0001",
) -> LineageProofRegistration:
    """Step 6 — register sealed proof in genesis lineage."""
    return LineageProofRegistration(
        lineage_root_id=lineage_root_id,
        vault_entry_id=vault_entry.id,
        chain_id=vault_entry.chain_id,
        proof_designation="CP-001",
    )


def run_avcp_ceremony(
    package: BoneKingProofPackage | None = None,
    *,
    observer: str = "Observer-01",
    founder_intervention: bool = False,
) -> CeremonyResult:
    """
    AVCP-1.0 ceremony — Vault is final authority; no founder may intervene.
    """
    if founder_intervention:
        raise RuntimeError("AVCP rule violated: founder intervention forbidden during ceremony")

    # Step 1 — load continuity package
    pkg = package or build_bone_king_proof_package()
    _ceremony_preconditions(pkg)

    # Step 2 — recompute invariants (trust boundaries)
    enforce_package_boundaries(pkg)

    # Step 3 — third-party reproduction
    reproduction = reproduce_package(pkg, observer=observer)
    log_entry = reproduction_log_entry(reproduction)
    if reproduction.result != "verified":
        handle_boundary_violation(pkg.chain_id, ["third_party_reproduction_failed"])
        raise RuntimeError(f"AVCP step 3 failed: {reproduction.details}")

    # Step 4 & 5 — apply D-3 seal and emit record
    vault_entry = VaultEntry(
        id=VAULT_CP_001,
        package_id=pkg.id,
        canonical_hash=pkg.canonical_hash,
        reproduction_log=[log_entry],
        status="verified",
    )
    seal_record = apply_d3_seal(pkg, reproduction, vault_entry_id=vault_entry.id)
    vault_entry = vault_entry.model_copy(update={"status": "sealed"})

    # Step 6 — genesis lineage registration
    lineage = register_continuity_proof_in_lineage(vault_entry)

    # Step 7 — announce to node
    announcement = CeremonyAnnouncement(
        vault_entry_id=vault_entry.id,
        seal_record_id=seal_record.id,
        chain_id=pkg.chain_id,
        canonical_hash=pkg.canonical_hash,
        message=(
            f"Continuity Proof CP-001 sealed under {seal_record.seal_id}. "
            "First verified fact in Continuity OS lineage."
        ),
    )

    return CeremonyResult(
        package=pkg,
        vault_entry=vault_entry,
        seal_record=seal_record,
        lineage_registration=lineage,
        announcement=announcement,
        reproduction_log=[log_entry],
    )
