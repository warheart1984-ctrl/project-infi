"""Tests for constitutional cockpit API and store helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.epoch_engine import run_epoch_cycle
from src.continuity.evidence_ledger import EvidenceLedgerStore, bootstrap_evidence_ledger
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


def test_law_store_epoch_and_lineages(ledger_paths) -> None:
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    assert law_store.get_current_epoch() >= 0
    lineages = law_store.get_lineages_for_law("PIT-1")
    assert len(lineages) >= 2


def test_evidence_lineage_graph(ledger_paths) -> None:
    law_store = LawLedgerStore()
    evidence_store = EvidenceLedgerStore()
    bootstrap_law_ledger(law_store)
    bootstrap_evidence_ledger(evidence_store)

    from src.continuity.evidence_ledger import evaluate_law_with_evidence

    pit = law_store.get_law("PIT-1")
    assert pit is not None
    lineages = law_store.get_lineages_for_law("PIT-1")
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=law_store,
        evidence_store=evidence_store,
    )

    graph = evidence_store.get_lineage_graph("EV-PIT-1-E3")
    assert graph["found"] is True
    assert graph["nodes"]
    assert graph["edges"]


def test_run_epoch_cycle(ledger_paths) -> None:
    result = run_epoch_cycle(signer="test-operator")
    assert result["status"] == "ok"
    assert result["epoch"] >= 1
    assert len(result["evaluated"]) == 3


def test_cockpit_api_routes(ledger_paths) -> None:
    from src.api import app

    client = app.test_client()
    summary = client.get("/api/cockpit/summary")
    assert summary.status_code == 200
    body = summary.get_json()
    assert body["law_count"] == 3
    assert "comprehension_health" in body
    assert "meaning_health" in body
    assert "evidence_fitness_health" in body
    assert "spine_commit_blocked" in body

    laws = client.get("/api/laws")
    assert laws.status_code == 200
    laws_body = laws.get_json()
    assert laws_body["count"] == 3
    first_law = laws_body["laws"][0]
    assert "chi" in first_law
    assert "mu" in first_law
    assert "omega" in first_law

    detail = client.get("/api/laws/PIT-1")
    assert detail.status_code == 200
    detail_body = detail.get_json()
    assert detail_body["law_id"] == "PIT-1"
    assert "cit_strip" in detail_body
    assert "meaning_strip" in detail_body

    evaluated = client.post("/api/laws/PIT-1/evaluate", json={"epoch": 4})
    assert evaluated.status_code == 200
    payload = evaluated.get_json()
    assert payload["status"] == "ok"
    assert payload["evidence_id"] == "EV-PIT-1-E4"
    assert "cit" in payload
    assert "mit" in payload

    eit = client.get("/api/eit/law/PIT-1")
    assert eit.status_code == 200
    assert "omega" in eit.get_json()

    trace = client.get("/api/trace/law/PIT-1")
    assert trace.status_code == 200
    assert trace.get_json()["found"] is True

    replay = client.post("/api/replay/law/PIT-1", json={"epoch": 4})
    assert replay.status_code == 200
    assert replay.get_json()["passed"] is True

    evidence = client.get(f"/api/evidence/{payload['evidence_id']}")
    assert evidence.status_code == 200
    evidence_body = evidence.get_json()
    assert evidence_body["found"] is True
    assert "eit_strip" in evidence_body

    epoch = client.post("/api/epoch/run", json={"signer": "operator"})
    assert epoch.status_code in {200, 409}
    if epoch.status_code == 200:
        assert epoch.get_json()["status"] == "ok"
