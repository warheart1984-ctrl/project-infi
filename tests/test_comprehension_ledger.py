"""Tests for CIT comprehension fitness and ledger."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.comprehension_fitness import (
    ComprehensionConfig,
    build_law_cit_strip,
    compute_chi,
    evaluate_drift,
    components_from_graph_metrics,
)
from src.continuity.comprehension_ledger import (
    ComprehensionLedgerStore,
    bootstrap_comprehension_ledger,
    build_comprehension_health,
    evaluate_law_comprehension,
    run_cit_proof,
)
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


def test_compute_chi_weighted_sum() -> None:
    components = components_from_graph_metrics(
        {
            "avg_hops": 1.0,
            "ambiguity_score": 0.0,
            "consequence_coverage": 1.0,
            "link_density": 1.0,
        }
    )
    chi = compute_chi(components, ComprehensionConfig())
    assert chi == pytest.approx(0.875, abs=0.001)


def test_cit2_drift_bounds() -> None:
    cfg = ComprehensionConfig(theta_min=0.75, delta_max=0.10)
    ok = evaluate_drift(0.82, 0.88, cfg=cfg)
    assert ok["status"] == "ok"
    assert "CIT-DRIFT" in evaluate_drift(0.70, 0.88, cfg=cfg)["warnings"]
    breach = evaluate_drift(0.60, 0.88, cfg=cfg)
    assert breach["status"] == "breach"
    assert "CIT-BLOCK" in breach["warnings"]


def test_law_cit_strip_for_founding_law() -> None:
    strip = build_law_cit_strip(
        {
            "law_id": "PIT-1",
            "status": "experimental",
            "fitness": {"current": 0.87},
            "dependencies": ["SIT-1", "GIT-1"],
            "domains": ["law-selection"],
            "conflicts": [],
        },
        evidence_id="EV-PIT-1-E3",
        epoch=3,
    )
    assert strip.chi >= 0.75
    assert strip.ready is True
    assert "PIT" in strip.constitutional_role


def test_comprehension_ledger_records_eval(ledger_paths) -> None:
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    comprehension = ComprehensionLedgerStore()
    bootstrap_comprehension_ledger(comprehension)

    pit = law_store.get_law("PIT-1")
    assert pit is not None
    result = evaluate_law_comprehension(pit.to_dict(), epoch=3, evidence_id="EV-PIT-1-E3", store=comprehension)
    assert result["record"]["chi"] >= 0.75
    assert result["entry"]["entry_type"] in {"CHI_EVAL", "CHI_DRIFT_ALERT", "CHI_THRESHOLD_BREACH"}


def test_comprehension_health_and_cit_api(ledger_paths) -> None:
    from src.api import app

    client = app.test_client()
    health = client.get("/api/cockpit/comprehension")
    assert health.status_code == 200
    body = health.get_json()
    assert body["avg_chi"] >= 0.75
    assert len(body["objects"]) == 3

    cit = client.get("/api/cockpit/cit/law/PIT-1")
    assert cit.status_code == 200
    assert cit.get_json()["cit_strip"]["object_id"] == "PIT-1"

    explain = client.get("/api/cockpit/explain/law/SIT-1")
    assert explain.status_code == 200
    assert explain.get_json()["explain"]


def test_run_cit_proof(ledger_paths) -> None:
    proof = run_cit_proof()
    assert proof["passed"] is True
