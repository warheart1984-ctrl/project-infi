"""Boundary port tests for Tri-Core / Nexus OS decoupling prep."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from nova.bridges import law_ledger_bridge, panel_store
from nova.bridges.panel_store import PanelStore
from src.aaes_os.nexus_execution_ledger import NexusExecutionLedger, reset_nexus_execution_ledger
from src.cori.evidence_factory import reset_evidence_factory
from src.continuity.continuity_store import ContinuityStore, reset_continuity_store
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
from src.governed.adapters import LocalNexusRecordAdapter, get_nexus_record_adapter
from src.governed.config import GovernedRuntimeConfig, reset_governed_config
from src.governed.darz_bridge import build_darz_receipt_from_urg
from src.governed.make_governed_mission import make_governed_mission
from src.governed.nexus_bridge import emit_nexus_event
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

    law_store = LawLedgerStore(path=law_path)
    bootstrap_law_ledger(law_store)
    law_ledger_bridge.reset_law_ledger_store(law_store)
    panel_store.reset_panel_store(PanelStore(path=panel_path))
    reset_continuity_store(ContinuityStore(path=continuity_path))
    reset_nexus_execution_ledger(NexusExecutionLedger(path=nexus_path))
    reset_evidence_factory(None)

    cfg = GovernedRuntimeConfig(
        use_http_nova=False,
        use_http_urg=False,
        use_http_aaes=False,
        mission_runtime=StubMissionRuntime(),
    )
    reset_governed_config(cfg)
    yield cfg
    reset_governed_config(None)
    law_ledger_bridge.reset_law_ledger_store(None)
    panel_store.reset_panel_store(None)
    reset_continuity_store(None)
    reset_nexus_execution_ledger(None)
    reset_evidence_factory(None)
    shutil.rmtree(runtime_dir, ignore_errors=True)


def test_null_nexus_record_adapter_skips_ledger() -> None:
    adapter = get_nexus_record_adapter("disabled")
    event = adapter.record_execution({"execution_id": "exec-1", "mission_id": "m-1"})
    assert event["status"] == "skipped"
    assert event["event_id"] == "exec-1"


def test_local_nexus_record_adapter_records() -> None:
    adapter = LocalNexusRecordAdapter()
    event = adapter.record_execution(
        {
            "execution_id": "exec-2",
            "trace_id": "trace-2",
            "mission_id": "mission-2",
            "law_eval_id": "law-2",
            "status": "executed",
        }
    )
    assert event["event_type"] == "execution"
    assert event.get("event_id")


def test_darz_nonstandard_tri_core_routing_authority_marks_violation() -> None:
    """Documents DAR-Z kernel coupling — authority must stay tri_core until kernel loosens."""
    cfg = GovernedRuntimeConfig(tri_core_routing_authority="tri_core.routing.dev")
    bundle = build_darz_receipt_from_urg(
        law_eval={"id": "law-1", "status": "ok"},
        urg_receipt={"mission_id": "m-1", "status": "ok"},
        steward_identity={"steward_id": "steward-1"},
        config=cfg,
    )
    assert "darz.bridge.tri_core_authority_missing" in bundle["receipt"]["violations"]


def test_darz_default_tri_core_routing_authority_accepted() -> None:
    bundle = build_darz_receipt_from_urg(
        law_eval={"id": "law-1", "status": "ok"},
        urg_receipt={"mission_id": "m-1", "status": "ok"},
        steward_identity={"steward_id": "steward-1"},
    )
    assert bundle["receipt"]["accepted"] is True


def test_governed_mission_with_nexus_record_disabled(governed_runtime: GovernedRuntimeConfig) -> None:
    cfg = GovernedRuntimeConfig(
        use_http_nova=False,
        use_http_urg=False,
        use_http_aaes=False,
        nexus_record_mode="disabled",
        mission_runtime=governed_runtime.mission_runtime,
        orchestrator=governed_runtime.orchestrator,
    )
    trace = make_governed_mission("boundary decoupling ping", config=cfg)
    assert trace["nexus_event"]["status"] == "skipped"
    assert trace["constitutional_trace"]["persistence"]["spine_boundary"]["nexus_record_mode"] == "disabled"


def test_emit_nexus_event_respects_config() -> None:
    reset_governed_config(GovernedRuntimeConfig(nexus_record_mode="disabled"))
    try:
        event = emit_nexus_event({"execution_id": "x-1"})
        assert event["status"] == "skipped"
    finally:
        reset_governed_config(None)
