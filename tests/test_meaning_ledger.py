"""Tests for MIT meaning fitness and ledger."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.meaning_fitness import MeaningConfig, build_law_meaning_strip, compute_mu
from src.continuity.mit_ledger import (
    MitLedgerStore,
    bootstrap_mit_ledger,
    evaluate_law_meaning,
    run_mit_proof,
)
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger


@pytest.fixture()
def ledger_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    law_path = tmp_path / "law-ledger.sqlite3"
    evidence_path = tmp_path / "evidence-ledger.sqlite3"
    comprehension_path = tmp_path / "comprehension-ledger.sqlite3"
    meaning_path = tmp_path / "mit-ledger.sqlite3"
    monkeypatch.setenv("LAW_LEDGER_PATH", str(law_path))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(evidence_path))
    monkeypatch.setenv("COMPREHENSION_LEDGER_PATH", str(comprehension_path))
    monkeypatch.setenv("MIT_LEDGER_PATH", str(meaning_path))
    return law_path, evidence_path, comprehension_path, meaning_path


def test_compute_mu_weighted_sum() -> None:
    from src.continuity.meaning_fitness import MeaningComponents

    components = MeaningComponents(
        M_purp=0.9,
        M_cons=0.85,
        M_stab=0.8,
        M_intent=0.88,
    )
    mu = compute_mu(components, MeaningConfig())
    assert mu == pytest.approx(0.8575, abs=0.001)


def test_law_meaning_strip_for_founding_law() -> None:
    strip = build_law_meaning_strip(
        {
            "law_id": "PIT-1",
            "status": "experimental",
            "fitness": {"current": 0.87, "history": [0.8, 0.85]},
            "domains": ["law-selection"],
        }
    )
    assert strip.mu >= 0.75
    assert strip.ready is True
    assert "PIT-1" in strip.intent_note or "PIT" in strip.canonical_meaning


def test_meaning_ledger_records_eval(ledger_paths) -> None:
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    meaning = MitLedgerStore()
    bootstrap_mit_ledger(meaning)
    bootstrap_mit_ledger(meaning)

    pit = law_store.get_law("PIT-1")
    assert pit is not None
    result = evaluate_law_meaning(pit.to_dict(), epoch=3, store=meaning)
    assert result["mu"] >= 0.75
    assert result["entry"]["entry_type"] in {"MIT_EVAL", "MIT_THRESHOLD_BREACH"}


def test_mit_api_routes(ledger_paths) -> None:
    from src.api import app

    client = app.test_client()
    mit = client.get("/api/mit/law/PIT-1")
    assert mit.status_code == 200
    body = mit.get_json()
    assert body["law_id"] == "PIT-1"
    assert body["mu"] >= 0.75

    explain = client.get("/api/explain/law/PIT-1")
    assert explain.status_code == 200
    payload = explain.get_json()
    assert payload["explain"]
    assert "meaning" in payload

    cit = client.get("/api/cit/law/PIT-1")
    assert cit.status_code == 200
    assert cit.get_json()["chi"] is not None

    detail = client.get("/api/laws/PIT-1")
    assert detail.status_code == 200
    detail_body = detail.get_json()
    assert detail_body["meaning_strip"]["mu"] >= 0.75
    assert detail_body["explain"]["summarize"]


def test_run_mit_proof(ledger_paths) -> None:
    proof = run_mit_proof()
    assert proof["passed"] is True
