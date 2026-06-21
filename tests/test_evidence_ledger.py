"""EIT-1 — Evidence Ledger and evidence-backed law evaluation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.evidence_ledger import (
    EVIDENCE_LEDGER_GENESIS_ENTRY_ID,
    EvidenceLedgerStore,
    EvidenceType,
    bootstrap_evidence_ledger,
    build_evidence_from_lineages,
    derive_components_from_evidence,
    evaluate_law_with_evidence,
    evidence_id_for,
    run_eit_proof,
    validate_decision_evidence,
)
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger, load_founding_laws
from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture


def test_build_and_derive_evidence() -> None:
    pit = load_founding_laws()[2]
    lineages = lineages_from_fixture(load_lci_fixture())
    evidence = build_evidence_from_lineages(pit, epoch=3, lineages=lineages, signer="kernel")
    assert evidence.evidence_id == "EV-PIT-1-E3"
    assert evidence.evidence_type == EvidenceType.DERIVATION
    assert evidence.canonical_hash
    components = derive_components_from_evidence(evidence)
    assert set(components) == {"C_cont", "C_conv", "C_inv", "C_safe"}


def test_evaluate_law_with_evidence_binds_proof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("LAW_LEDGER_PATH", str(online / "law-ledger.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence-ledger.sqlite3"))

    law_store = LawLedgerStore()
    evidence_store = EvidenceLedgerStore()
    bootstrap_law_ledger(law_store)
    bootstrap_evidence_ledger(evidence_store)

    pit = law_store.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture())
    evaluated = evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=law_store,
        evidence_store=evidence_store,
    )
    assert evaluated.current_fitness > 0.0

    eval_entries = [
        item
        for item in law_store.ledger_entries()
        if item.payload.get("type") == "LAW_EVAL" and item.law_id == "PIT-1"
    ]
    assert eval_entries[-1].payload["evidence_id"] == evidence_id_for("PIT-1", 3)
    validation = validate_decision_evidence(eval_entries[-1].payload, evidence_store=evidence_store)
    assert validation["passed"] is True

    stored = evidence_store.get_evidence(evidence_id_for("PIT-1", 3))
    assert stored is not None
    assert stored.trace_links


def test_run_eit_proof_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("LAW_LEDGER_PATH", str(online / "law-ledger.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence-ledger.sqlite3"))

    first = run_eit_proof()
    second = run_eit_proof()
    assert first["passed"] is True
    assert first["genesis_ok"] is True
    assert first["evidence_bound"] is True
    assert second["passed"] is True
    assert any(
        item.entry_id == EVIDENCE_LEDGER_GENESIS_ENTRY_ID
        for item in EvidenceLedgerStore().ledger_entries()
    )
