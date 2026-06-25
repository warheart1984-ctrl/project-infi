"""Tests for CP-001 vault entry, D-3 seal, AVCP ceremony, and CTS boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.cori.vault.avcp import run_avcp_ceremony
from src.cori.vault.canonical import compute_package_hash
from src.cori.vault.cts import (
    BoundaryViolationError,
    enforce_package_boundaries,
    handle_boundary_violation,
)
from src.cori.vault.models import D3_SEAL_REC_1, VAULT_CP_001
from src.cori.vault.package import build_bone_king_proof_package
from src.cori.vault.reproduce import reproduce_package
from src.cori.vault.seal import D3_CRITERIA, apply_d3_seal
from src.cori.vault.store import VaultStorage


@pytest.fixture()
def vault_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db = tmp_path / "vault.sqlite3"
    monkeypatch.setenv("VAULT_STORE_PATH", str(db))
    return db


def test_bone_king_package_has_stable_ids() -> None:
    package = build_bone_king_proof_package()
    assert package.id == "BK-PKG-1"
    assert package.chain_id == "CHAIN-BK-1"
    assert package.artifacts.memory.id == "WMR-1"
    assert package.artifacts.derived_claim.id == "WCLAIM-1"
    assert package.artifacts.claim_record.id == "WCR-1"
    assert package.artifacts.verification.id == "WVERIF-1"
    assert package.canonical_hash
    assert len(package.canonical_hash) == 64


def test_package_hash_is_deterministic() -> None:
    a = build_bone_king_proof_package()
    b = build_bone_king_proof_package()
    assert a.canonical_hash == b.canonical_hash
    assert compute_package_hash(a.artifacts) == a.canonical_hash


def test_rp10_reproduction_verifies() -> None:
    package = build_bone_king_proof_package()
    result = reproduce_package(package, observer="Observer-01")
    assert result.result == "verified"
    assert result.details["canonical_hash_match"] is True
    assert result.details["state_match"] is True


def test_d3_seal_application() -> None:
    package = build_bone_king_proof_package()
    reproduction = reproduce_package(package)
    seal = apply_d3_seal(package, reproduction, vault_entry_id=VAULT_CP_001)
    assert seal.id == D3_SEAL_REC_1
    assert seal.canonical_hash == package.canonical_hash
    assert seal.criteria_satisfied == D3_CRITERIA


def test_cts_boundaries_pass_for_bone_king() -> None:
    package = build_bone_king_proof_package()
    result = enforce_package_boundaries(package)
    assert result.passed
    assert len(result.violations) == 0


def test_cts_violation_triggers_safeguard() -> None:
    state = handle_boundary_violation("CHAIN-BK-1", ["hidden_state"])
    assert state.active
    assert "CHAIN-BK-1" in state.quarantined_chains


def test_avcp_ceremony_full_chain(vault_db: Path) -> None:
    result = run_avcp_ceremony()
    assert result.vault_entry.id == VAULT_CP_001
    assert result.vault_entry.status == "sealed"
    assert result.seal_record.canonical_hash == result.package.canonical_hash
    assert result.reproduction_log[0].result == "verified"
    assert "Bone King" in result.announcement.message or "CP-001" in result.announcement.message

    storage = VaultStorage(vault_db)
    storage.persist_ceremony(
        result.package,
        result.vault_entry,
        result.seal_record,
        result.lineage_registration,
    )
    loaded = storage.get_vault_entry(VAULT_CP_001)
    assert loaded.status == "sealed"
    assert loaded.canonical_hash == result.package.canonical_hash


def test_avcp_rejects_founder_intervention() -> None:
    with pytest.raises(RuntimeError, match="founder intervention"):
        run_avcp_ceremony(founder_intervention=True)


def test_cts_enforce_raises_on_tampered_verification() -> None:
    package = build_bone_king_proof_package()
    bad = package.model_copy(
        update={
            "artifacts": package.artifacts.model_copy(
                update={
                    "verification": package.artifacts.verification.model_copy(
                        update={"status": "failed"}
                    )
                }
            )
        }
    )
    with pytest.raises(BoundaryViolationError):
        enforce_package_boundaries(bad)


def test_category_b_closure_registers_mission_completion(vault_db: Path) -> None:
    from src.cori.vault.category_b import load_bone_king_package_from_bundle, run_category_b_closure
    from src.cori.vault.models import BK_CANONICAL_HASH, MISSION_001

    result = run_category_b_closure(observer="Bradley")
    assert result.package.canonical_hash == BK_CANONICAL_HASH
    assert result.vault_entry.status == "completed"
    assert result.seal_record.founder_independent is True
    assert result.seal_record.reproduction_category == "B"
    assert result.mission_completion.status == "COMPLETED"
    assert result.mission_dossier.state == "CLOSED"
    assert result.observer_report.observer == "Bradley"
    assert len(result.observer_report.criteria) == 7
    assert all(c.satisfied for c in result.observer_report.criteria)

    storage = VaultStorage(vault_db)
    storage.persist_category_b_closure(
        result.package,
        result.vault_entry,
        result.seal_record,
        result.lineage_registration,
        result.observer_report,
        result.mission_completion,
        result.ceremony_completion,
        result.trust_boundary_update,
        result.mission_dossier,
    )
    loaded = storage.get_vault_entry(VAULT_CP_001)
    assert loaded.status == "completed"
    assert loaded.canonical_hash == BK_CANONICAL_HASH

    bundle_pkg = load_bone_king_package_from_bundle()
    assert bundle_pkg.mission_id == MISSION_001
