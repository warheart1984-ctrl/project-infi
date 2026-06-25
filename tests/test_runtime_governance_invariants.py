"""Runtime governance invariant tests for CORI Alpha."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from nova.bridges import law_ledger_bridge, panel_store
from nova.bridges.panel_store import PanelStore
from src.aaes_os.nexus_execution_ledger import NexusExecutionLedger, reset_nexus_execution_ledger
from src.continuity.continuity_store import ContinuityStore, reset_continuity_store
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
from src.cori.asset_registry import reset_asset_registry
from src.cori.evidence_factory import EvidenceFactory, reset_evidence_factory
from src.cori.governance_invariants import GovernanceInvariantChecker
from src.governed.config import GovernedRuntimeConfig, reset_governed_config
from src.governed.make_governed_mission import make_governed_mission
from tests.governed_stubs import StubMissionRuntime


@pytest.fixture()
def governed_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    panel_path = tmp_path / "nova_panel_store.sqlite3"
    law_path = tmp_path / "law-ledger.sqlite3"
    continuity_path = tmp_path / "continuity.sqlite3"
    nexus_path = tmp_path / "nexus_executions.jsonl"

    monkeypatch.setenv("AAIS_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("NOVA_PANEL_STORE_PATH", str(panel_path))
    monkeypatch.setenv("LAW_LEDGER_PATH", str(law_path))
    monkeypatch.setenv("CONTINUITY_STORE_PATH", str(continuity_path))
    monkeypatch.setenv("NEXUS_EXECUTION_LEDGER_PATH", str(nexus_path))
    monkeypatch.setenv("URG_OPERATOR_RECEIPT_KEY", "test-receipt-key-fixed")
    monkeypatch.setenv("URG_RECEIPT_SIGNING_KEY", "test-urg-receipt-key-fixed")
    monkeypatch.setenv("GOVERNED_NOVA_IN_PROCESS", "1")
    monkeypatch.setenv("GOVERNED_URG_IN_PROCESS", "1")
    monkeypatch.setenv("GOVERNED_AAES_IN_PROCESS", "1")

    continuity = ContinuityStore(path=continuity_path)
    law_store = LawLedgerStore(path=law_path)
    bootstrap_law_ledger(law_store)
    law_ledger_bridge.reset_law_ledger_store(law_store)
    panel_store.reset_panel_store(PanelStore(path=panel_path))
    reset_continuity_store(continuity)
    reset_asset_registry()
    reset_evidence_factory(EvidenceFactory(continuity=continuity))
    reset_nexus_execution_ledger(NexusExecutionLedger(path=nexus_path))

    cfg = GovernedRuntimeConfig(
        use_http_nova=False,
        use_http_urg=False,
        use_http_aaes=False,
        mission_tenant_id="tenant:acme",
        aais_instance_id="aais-local-1",
        mission_runtime=StubMissionRuntime(),
    )
    reset_governed_config(cfg)

    yield {
        "config": cfg,
        "continuity": continuity,
        "law_store": law_store,
    }

    reset_governed_config(None)
    law_ledger_bridge.reset_law_ledger_store(None)
    panel_store.reset_panel_store(None)
    reset_continuity_store(None)
    reset_asset_registry(None)
    reset_evidence_factory(None)
    reset_nexus_execution_ledger(None)
    shutil.rmtree(runtime_dir, ignore_errors=True)


def _checker(runtime: dict) -> GovernanceInvariantChecker:
    return GovernanceInvariantChecker(
        continuity=runtime["continuity"],
        law_store=runtime["law_store"],
    )


def test_invariant_no_execution_without_validation(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: execution requires validation.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    result = _checker(governed_runtime).check_no_execution_without_validation()
    assert result.passed, result.violations


def test_invariant_no_validation_without_evidence(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: validation requires evidence.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    result = _checker(governed_runtime).check_no_validation_without_evidence()
    assert result.passed, result.violations


def test_invariant_no_governed_mission_without_law_eval(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: governed mission requires law eval.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    result = _checker(governed_runtime).check_no_governed_mission_without_law_eval()
    assert result.passed, result.violations


def test_invariant_nova_laws_have_ledger_hash(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: nova laws have ledger hash.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    result = _checker(governed_runtime).check_nova_laws_have_ledger_hash()
    assert result.passed, result.violations


def test_invariant_panels_match_continuity(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: panels match continuity.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    result = _checker(governed_runtime).check_panels_match_continuity()
    assert result.passed, result.violations


def test_all_invariants_pass_and_persist_status(governed_runtime: dict) -> None:
    make_governed_mission(
        "Invariant test: full suite.",
        {"operator_id": "operator-inv", "steward_id": "steward-inv"},
        config=governed_runtime["config"],
    )
    checker = _checker(governed_runtime)
    results = checker.run_all()
    checker.persist_status(results)
    assert all(r.passed for r in results), [r.to_dict() for r in results if not r.passed]
    status = checker.list_status()
    assert len(status) == len(results)
    assert all(row["status"] == "pass" for row in status)
