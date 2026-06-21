"""Tests for EIT-2 evidence fitness, cross-ledger trace, and replay."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.constitutional_cockpit_routes import build_cockpit_summary
from src.continuity.cross_ledger_trace import build_cross_ledger_trace, replay_law_evidence
from src.continuity.evidence_fitness import (
    EvidenceFitnessConfig,
    build_evidence_eit_strip,
    build_evidence_fitness_health,
    compute_omega,
    components_from_evidence_record,
    evaluate_eit2_convergence,
    run_eit2_proof,
)
from src.continuity.evidence_ledger import (
    EvidenceLedgerStore,
    bootstrap_evidence_ledger,
    evaluate_law_with_evidence,
    evidence_id_for,
)
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
from src.continuity.lci_stack import LCI_FIXTURE, lineages_from_fixture, load_lci_fixture


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


def test_compute_omega_weighted_sum() -> None:
    components = components_from_evidence_record(
        {
            "evidence_id": "EV-PIT-1-E3",
            "evidence_type": "derivation",
            "validation_method": "lci_stack_replay",
            "canonical_hash": "abc123",
            "trace_links": ["L0", "L1"],
            "law_id": "PIT-1",
            "confidence": 0.95,
            "_components": {"stability": 0.9},
            "_sample_size": 3,
            "dependencies": ["SIT-1"],
        }
    )
    omega = compute_omega(components, EvidenceFitnessConfig())
    assert omega >= 0.70


def test_eit2_operator_convergence() -> None:
    from src.continuity.evidence_ledger import build_evidence_from_lineages

    laws = LawLedgerStore()
    bootstrap_law_ledger(laws)
    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    built = build_evidence_from_lineages(pit, 3, lineages, signer="operator")
    result = evaluate_eit2_convergence(built, replayed=built)
    assert result["operator_convergent"] is True
    assert result["status"] == "ok"


def test_cross_ledger_trace_for_founding_law(ledger_paths) -> None:
    laws = LawLedgerStore()
    evidence = EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=laws,
        evidence_store=evidence,
    )

    trace = build_cross_ledger_trace("PIT-1", law_store=laws, evidence_store=evidence)
    assert trace["found"] is True
    assert trace["evidence_id"] == evidence_id_for("PIT-1", 3)
    layers = {node["layer"] for node in trace["nodes"]}
    assert "law" in layers
    assert "evidence" in layers


def test_replay_law_evidence_converges(ledger_paths) -> None:
    laws = LawLedgerStore()
    evidence = EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=laws,
        evidence_store=evidence,
    )

    replay = replay_law_evidence("PIT-1", epoch=3, law_store=laws, evidence_store=evidence)
    assert replay["passed"] is True
    assert replay["operator_convergent"] is True


def test_evidence_fitness_health_after_eval(ledger_paths) -> None:
    laws = LawLedgerStore()
    evidence = EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)

    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=laws,
        evidence_store=evidence,
    )

    health = build_evidence_fitness_health(law_store=laws, evidence_store=evidence)
    assert health["avg_omega"] >= EvidenceFitnessConfig().theta_evidence


def test_cockpit_summary_includes_spine_health(ledger_paths) -> None:
    summary = build_cockpit_summary()
    assert "meaning_health" in summary
    assert "evidence_fitness_health" in summary
    assert summary["meaning_health"]["avg_mu"] >= 0
    assert summary["evidence_fitness_health"]["avg_omega"] >= 0


def test_run_eit2_proof(ledger_paths) -> None:
    laws = LawLedgerStore()
    evidence = EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)
    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=laws,
        evidence_store=evidence,
    )
    proof = run_eit2_proof(law_store=laws, evidence_store=evidence)
    assert proof["passed"] is True


def test_build_evidence_eit_strip(ledger_paths) -> None:
    laws = LawLedgerStore()
    evidence = EvidenceLedgerStore()
    bootstrap_law_ledger(laws)
    bootstrap_evidence_ledger(evidence)
    pit = laws.get_law("PIT-1")
    assert pit is not None
    lineages = lineages_from_fixture(load_lci_fixture(LCI_FIXTURE))
    evaluate_law_with_evidence(
        pit,
        epoch=3,
        lineages=lineages,
        law_store=laws,
        evidence_store=evidence,
    )
    stored = evidence.get_evidence(evidence_id_for("PIT-1", 3))
    assert stored is not None
    graph = evidence.get_lineage_graph(stored.evidence_id)
    strip = build_evidence_eit_strip(stored, graph=graph)
    assert strip.omega >= EvidenceFitnessConfig().theta_evidence
    assert strip.ready is True
