"""Law Ledger — genesis block, founding laws, sovereign selection kernel."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.law_ledger import (
    LAW_LEDGER_GENESIS_ENTRY_ID,
    LawLedgerEntryType,
    LawLedgerStore,
    LawStatus,
    bootstrap_law_ledger,
    evaluate_law,
    genesis_block,
    law_eval_payload,
    law_status_change_payload,
    load_founding_laws,
    run_law_ledger_proof,
)
from src.continuity.lci_stack import lineages_from_fixture, load_lci_fixture


def test_genesis_block_shape() -> None:
    block = genesis_block()
    assert block.entry_id == LAW_LEDGER_GENESIS_ENTRY_ID
    assert block.prev_hash is None
    assert block.entry_type.value == "LAW_GENESIS"
    assert block.payload["initialized_laws"] == ["SIT-1"]


def test_founding_laws_fixture() -> None:
    laws = load_founding_laws()
    assert [item.law_id for item in laws] == ["SIT-1", "GIT-1", "PIT-1"]
    sit, git, pit = laws
    assert sit.status == LawStatus.ADMITTED
    assert git.status == LawStatus.ADMITTED
    assert pit.status == LawStatus.EXPERIMENTAL
    assert pit.current_fitness == 0.87
    assert pit.admit_threshold == 0.9
    assert pit.reject_threshold == 0.7


def test_payload_schemas() -> None:
    eval_payload = law_eval_payload(
        law_id="PIT-1",
        law_hash="hash_pit1_v1",
        epoch=2,
        f=0.87,
        components={"C_cont": 0.9, "C_conv": 0.85, "C_inv": 0.88, "C_safe": 0.86},
        sample_size=20,
        thresholds={"admit": 0.9, "reject": 0.7},
        notes="Initial generative fitness tests",
    )
    assert eval_payload["type"] == "LAW_EVAL"
    assert eval_payload["fitness"]["F"] == 0.87

    status_payload = law_status_change_payload(
        law_id="PIT-1",
        law_hash="hash_pit1_v1",
        epoch=2,
        old_status=LawStatus.PROPOSED,
        new_status=LawStatus.EXPERIMENTAL,
        reason="F(G)=0.870 with thresholds={'admit': 0.9, 'reject': 0.7}",
        source="kernel",
        ref_entry_id="LAW-LEDGER-0002",
    )
    assert status_payload["type"] == "LAW_STATUS_CHANGE"
    assert status_payload["new_status"] == "experimental"


def test_bootstrap_and_evaluate_law(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    db_path = online / "law-ledger.sqlite3"
    monkeypatch.setenv("LAW_LEDGER_PATH", str(db_path))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence-ledger.sqlite3"))

    store = LawLedgerStore()
    bootstrap = bootstrap_law_ledger(store)
    assert bootstrap["genesis_entry_id"] == LAW_LEDGER_GENESIS_ENTRY_ID
    assert bootstrap["law_count"] == 3

    entries = store.ledger_entries()
    assert entries[0].entry_id == LAW_LEDGER_GENESIS_ENTRY_ID
    assert entries[0].prev_hash is None

    pit = store.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture())
    evaluated = evaluate_law(pit, epoch=3, lineages=lineages, store=store)
    assert evaluated.current_fitness > 0.0

    eval_entries = [item for item in store.ledger_entries() if item.entry_type == LawLedgerEntryType.LAW_EVAL]
    assert len(eval_entries) >= 1
    assert eval_entries[-1].payload["type"] == "LAW_EVAL"
    assert eval_entries[-1].payload.get("evidence_id")


def test_run_law_ledger_proof_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("LAW_LEDGER_PATH", str(online / "law-ledger.sqlite3"))

    first = run_law_ledger_proof()
    second = run_law_ledger_proof()
    assert first["passed"] is True
    assert first["founding_laws_ok"] is True
    assert second["passed"] is True
    assert second["ledger_entry_count"] == first["ledger_entry_count"]
