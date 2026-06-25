"""Tests for Constitutional Runtime v0.1 — DecisionObject, OutcomeObject, OIT spine."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.continuity.decision_ledger import (
    DecisionLedgerStore,
    DecisionRecord,
    DecisionStatus,
    bootstrap_decision_ledger,
)
from src.continuity.outcome_fitness import (
    OutcomeConfig,
    build_outcome_health,
    classify_variance,
    compute_outcome_drift,
    compute_variance,
)
from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger


@pytest.fixture
def runtime_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("AAIS_ONLINE_RUNTIME_DIR", str(online))
    monkeypatch.setenv("DECISION_LEDGER_PATH", str(online / "decision.sqlite3"))
    monkeypatch.setenv("OUTCOME_LEDGER_PATH", str(online / "outcome.sqlite3"))
    monkeypatch.setenv("LAW_LEDGER_PATH", str(online / "law.sqlite3"))
    monkeypatch.setenv("EVIDENCE_LEDGER_PATH", str(online / "evidence.sqlite3"))
    monkeypatch.setenv("COMPREHENSION_LEDGER_PATH", str(online / "comprehension.sqlite3"))
    monkeypatch.setenv("MIT_LEDGER_PATH", str(online / "mit.sqlite3"))
    monkeypatch.setenv("SIT_LEDGER_PATH", str(online / "sit.sqlite3"))
    monkeypatch.setenv("GIT_LEDGER_PATH", str(online / "git.sqlite3"))
    return online


def test_decision_lifecycle(runtime_dirs: Path) -> None:
    store = DecisionLedgerStore()
    bootstrap_decision_ledger(store, epoch=17)
    record = store.get("DEC-2026-0001")
    assert record is not None
    assert record.status == DecisionStatus.EXECUTED
    assert "phase-17" in record.tags


def test_outcome_variance_and_drift(runtime_dirs: Path) -> None:
    store = OutcomeLedgerStore()
    bootstrap_outcome_ledger(store, epoch=17)
    outcome = store.get("OUT-2026-0007")
    assert outcome is not None
    assert outcome.variance.get("classification") == "acceptable"
    drift = compute_outcome_drift(store.list_outcomes())
    assert drift == 0.0


def test_outcome_health_in_spine(runtime_dirs: Path) -> None:
    from src.continuity.evidence_fitness import build_spine_health

    OutcomeLedgerStore()
    bootstrap_outcome_ledger(OutcomeLedgerStore())
    spine = build_spine_health()
    assert "outcome_health" in spine
    assert "outcome_drift" in spine
    assert "overall" in spine
    assert spine["outcome_drift"] == 0.0


def test_build_cockpit_summary_includes_outcome(runtime_dirs: Path) -> None:
    from src.constitutional_cockpit_routes import build_cockpit_summary

    summary = build_cockpit_summary()
    assert summary["outcome_health"]["outcome_drift"] == 0.0
    assert summary["spine_overall"] is not None
    assert "boundary_detection" in summary
    assert "reference_integrity" in summary


def _flask_app():
    import importlib.util
    from functools import lru_cache
    from pathlib import Path

    @lru_cache(maxsize=1)
    def _load() -> object:
        api_path = Path(__file__).resolve().parents[1] / "src" / "api.py"
        spec = importlib.util.spec_from_file_location("src_flask_api", api_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module.app

    return _load()


def test_decision_api(runtime_dirs: Path) -> None:
    app = _flask_app()

    client = app.test_client()
    response = client.get("/api/decisions/DEC-2026-0001")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["id"] == "DEC-2026-0001"
    assert payload.get("outcome_strip") is not None


def test_outcome_api(runtime_dirs: Path) -> None:
    app = _flask_app()

    client = app.test_client()
    response = client.get("/api/outcomes/OUT-2026-0007")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["decision_id"] == "DEC-2026-0001"
    assert payload["outcome_strip"]["variance_classification"] == "acceptable"


def test_constitutional_runtime_advance_epoch(runtime_dirs: Path) -> None:
    from src.continuity.constitutional_runtime import ConstitutionalLedgers, ConstitutionalRuntime
    from src.constitutional_cockpit_routes import _ensure_ledgers

    law_store, evidence_store, comprehension_store, meaning_store, sit_store, git_store = _ensure_ledgers()
    ledgers = ConstitutionalLedgers(
        law_store=law_store,
        evidence_store=evidence_store,
        comprehension_store=comprehension_store,
        mit_store=meaning_store,
        sit_store=sit_store,
        git_store=git_store,
        epoch=17,
    )
    runtime = ConstitutionalRuntime(ledgers)
    result = runtime.advance_epoch()
    assert result["epoch"] == 18
    assert "spine_health" in result


def test_critical_outcome_blocks_spine() -> None:
    variance = compute_variance(
        {"metrics": {"spine_health_delta": 0.12}},
        {"metrics": {"spine_health_delta": 0.0}},
    )
    assert classify_variance(variance) == "concerning"
    severe = compute_variance(
        {"metrics": {"spine_health_delta": 0.20}},
        {"metrics": {"spine_health_delta": 0.0}},
    )
    assert classify_variance(severe) == "critical"
