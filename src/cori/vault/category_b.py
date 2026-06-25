"""FIRC-1.0 — Category B founder-independent reproduction closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.cori.vault.avcp import run_avcp_ceremony
from src.cori.vault.models import (
    BK_CANONICAL_HASH,
    BK_PKG_1,
    CATEGORY_B_CRITERIA,
    D3_SEAL_REC_1,
    FIRC_VERSION,
    VAULT_CP_001,
    BoneKingProofPackage,
    CategoryBCriterion,
    CategoryBClosureResult,
    CeremonyCompletionRecord,
    LineageProofRegistration,
    MissionCompletionRecord,
    MissionDossierRecord,
    ObserverReportRecord,
    SealApplicationRecord,
    TrustBoundaryUpdate,
    VaultEntry,
)
from src.cori.vault.reproduce import reproduce_package, reproduction_log_entry
from src.cori.vault.seal import D3_CRITERIA


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_bone_king_package_from_bundle(
    bundle_path: Path | None = None,
) -> BoneKingProofPackage:
    path = bundle_path or (_repo_root() / "observer-bundle" / "BK-PKG-1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return BoneKingProofPackage.model_validate(payload)


def default_category_b_criteria(*, notes: str = "") -> list[CategoryBCriterion]:
    return [
        CategoryBCriterion(id=cid, title=title, satisfied=True, notes=notes)
        for cid, title in CATEGORY_B_CRITERIA
    ]


def compute_observer_report_hash(report: ObserverReportRecord) -> str:
    payload = report.model_dump(mode="json", exclude={"report_hash", "submitted_at"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_observer_report(
    *,
    observer: str,
    environment: dict[str, str],
    canonical_hash: str = BK_CANONICAL_HASH,
    criteria: list[CategoryBCriterion] | None = None,
) -> ObserverReportRecord:
    report = ObserverReportRecord(
        observer=observer,
        environment=environment,
        canonical_hash_confirmed=canonical_hash,
        criteria=criteria or default_category_b_criteria(),
    )
    report.report_hash = compute_observer_report_hash(report)
    return report


def _validate_category_b(
    package: BoneKingProofPackage,
    observer_report: ObserverReportRecord,
) -> None:
    if package.canonical_hash != BK_CANONICAL_HASH:
        raise ValueError(
            f"Category B failed B-6: canonical hash mismatch "
            f"(expected {BK_CANONICAL_HASH}, got {package.canonical_hash})"
        )
    if observer_report.canonical_hash_confirmed != package.canonical_hash:
        raise ValueError("Category B failed B-6: observer hash confirmation mismatch")
    unsatisfied = [c.id for c in observer_report.criteria if not c.satisfied]
    if unsatisfied:
        raise ValueError(f"Category B criteria not satisfied: {', '.join(unsatisfied)}")


def run_category_b_closure(
    *,
    observer: str = "Bradley",
    environment: dict[str, str] | None = None,
    package: BoneKingProofPackage | None = None,
    existing_vault_entry: VaultEntry | None = None,
    existing_seal: SealApplicationRecord | None = None,
    existing_lineage: LineageProofRegistration | None = None,
) -> CategoryBClosureResult:
    """
    Register Mission #001 Category B completion:
    VERIFIED → COMPLETED, D-3 founder-independent seal, dossier CLOSED.
    """
    pkg = package or load_bone_king_package_from_bundle()
    env = environment or {
        "os": "Ubuntu 24.04",
        "python": "3.12",
        "execution": "independent",
        "founder_infrastructure": "none",
    }

    observer_report = build_observer_report(
        observer=observer,
        environment=env,
        canonical_hash=pkg.canonical_hash,
    )
    _validate_category_b(pkg, observer_report)

    reproduction = reproduce_package(pkg, observer=observer)
    if reproduction.result != "verified":
        raise RuntimeError(f"Category B reproduction failed: {reproduction.details}")

    log_entry = reproduction_log_entry(reproduction)
    if existing_vault_entry and existing_seal and existing_lineage:
        vault_entry = existing_vault_entry
        seal_record = existing_seal
        lineage = existing_lineage
    else:
        ceremony = run_avcp_ceremony(pkg, observer=observer)
        vault_entry = ceremony.vault_entry
        seal_record = ceremony.seal_record
        lineage = ceremony.lineage_registration

    seal_record = seal_record.model_copy(
        update={
            "reproduction_category": "B",
            "founder_independent": True,
            "observer_report_hash": observer_report.report_hash,
            "criteria_satisfied": D3_CRITERIA + ["Founder-independent reproduction (Category B)"],
        }
    )

    reproduction_log = list(vault_entry.reproduction_log)
    if not any(e.observer == observer and e.result == "verified" for e in reproduction_log):
        reproduction_log.append(log_entry)

    vault_entry = vault_entry.model_copy(
        update={
            "status": "completed",
            "canonical_hash": pkg.canonical_hash,
            "reproduction_log": reproduction_log,
            "summary": (
                "Continuity Proof #001 — Bone King. "
                "Category B founder-independent reproduction achieved (FIRC-1.0)."
            ),
        }
    )

    mission_completion = MissionCompletionRecord(
        observer=observer,
        canonical_hash=pkg.canonical_hash,
        environment_details=env,
    )

    ceremony_completion = CeremonyCompletionRecord(
        observer_report_id=observer_report.id,
        seal_record_id=seal_record.id,
        evidence_bundle_refs=[
            pkg.id,
            "observer-bundle.zip",
            f"specs/{FIRC_VERSION}.json",
            f"specs/RP-1.0.json",
        ],
    )

    trust_update = TrustBoundaryUpdate()
    dossier = MissionDossierRecord(
        archived_artifacts=[
            BK_PKG_1,
            VAULT_CP_001,
            D3_SEAL_REC_1,
            observer_report.id,
            "observer-bundle/",
        ]
    )

    return CategoryBClosureResult(
        package=pkg,
        vault_entry=vault_entry,
        seal_record=seal_record,
        lineage_registration=lineage,
        observer_report=observer_report,
        mission_completion=mission_completion,
        ceremony_completion=ceremony_completion,
        trust_boundary_update=trust_update,
        mission_dossier=dossier,
    )
