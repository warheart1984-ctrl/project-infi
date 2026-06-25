"""Tests for SIT, GIT, PIT spine layers (Phases 18–20)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.continuity.evidence_fitness import build_spine_health
from src.continuity.git_fitness import compute_lambda, components_from_lineages
from src.continuity.git_ledger import GitLedgerStore, bootstrap_git_ledger, run_git_fitness_proof
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
from src.continuity.pit_fitness import build_pit_health, run_pit_proof
from src.continuity.sit_ledger import SitLedgerStore, bootstrap_sit_ledger, run_sit_proof
from src.continuity.structural_fitness import compute_sigma, components_from_law_context


@pytest.fixture()
def spine_ledger_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LAW_LEDGER_PATH", str(tmp_path / "law-ledger.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(tmp_path / "evidence-ledger.sqlite3"))
    monkeypatch.setenv("COMPREHENSION_LEDGER_PATH", str(tmp_path / "comprehension-ledger.sqlite3"))
    monkeypatch.setenv("MIT_LEDGER_PATH", str(tmp_path / "mit-ledger.sqlite3"))
    monkeypatch.setenv("SIT_LEDGER_PATH", str(tmp_path / "sit-ledger.sqlite3"))
    monkeypatch.setenv("GIT_LEDGER_PATH", str(tmp_path / "git-ledger.sqlite3"))


def test_compute_sigma_weighted_sum() -> None:
    components = components_from_law_context(
        {"law_id": "PIT-1", "status": "sovereign", "current_fitness": 0.87},
        lineage_count=3,
        graph={"nodes": [{"id": "n1"}], "edges": [{"from": "n1", "to": "n2"}]},
        evidence_present=True,
    )
    sigma = compute_sigma(components)
    assert 0.0 <= sigma <= 1.0
    assert sigma >= 0.7


def test_git_components_from_lineages() -> None:
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    lineages = law_store.get_lineages_for_law("GIT-1")
    components, generative_law, passed = components_from_lineages(lineages)
    lambda_value = compute_lambda(components)
    assert generative_law
    assert 0.0 <= lambda_value <= 1.0
    assert passed is True


def test_build_spine_health_includes_sit_git_pit(spine_ledger_paths) -> None:
    spine = build_spine_health()
    assert "structural_health" in spine
    assert "generative_health" in spine
    assert "proof_health" in spine
    assert spine["structural_health"]["avg_sigma"] > 0
    assert spine["generative_health"]["avg_lambda"] > 0
    assert spine["proof_health"]["avg_phi"] > 0


def test_sit_git_pit_proofs(spine_ledger_paths) -> None:
    sit = run_sit_proof(store=SitLedgerStore())
    git = run_git_fitness_proof(store=GitLedgerStore())
    pit = run_pit_proof()
    assert sit["passed"] is True
    assert git["passed"] is True
    assert pit["passed"] is True


def test_pit_health_phi_from_law_fitness(spine_ledger_paths) -> None:
    law_store = LawLedgerStore()
    bootstrap_law_ledger(law_store)
    health = build_pit_health(law_store=law_store)
    pit = next(item for item in health["objects"] if item["object_id"] == "PIT-1")
    assert pit["phi"] >= 0.7


def test_cockpit_spine_and_layer_routes(spine_ledger_paths) -> None:
    from src.api import app

    client = app.test_client()
    spine = client.get("/api/cockpit/spine")
    assert spine.status_code == 200
    body = spine.get_json()
    assert "structural_health" in body
    assert "generative_health" in body
    assert "proof_health" in body

    summary = client.get("/api/cockpit/summary").get_json()
    assert "structural_health" in summary
    assert "generative_health" in summary
    assert "proof_health" in summary

    sit = client.get("/api/sit/law/PIT-1").get_json()
    git = client.get("/api/git/law/PIT-1").get_json()
    pit = client.get("/api/pit/law/PIT-1").get_json()
    assert sit["sigma"] is not None
    assert git["lambda"] is not None
    assert pit["phi"] is not None

    detail = client.get("/api/laws/PIT-1").get_json()
    assert "sit_strip" in detail
    assert "git_strip" in detail
    assert "pit_strip" in detail

    laws = client.get("/api/laws").get_json()["laws"][0]
    assert "sigma" in laws
    assert "lambda" in laws
    assert "phi" in laws

    bootstrap_sit_ledger(SitLedgerStore())
    bootstrap_git_ledger(GitLedgerStore())
