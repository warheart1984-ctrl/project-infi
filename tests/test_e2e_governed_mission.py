"""End-to-end governed constitutional spine: Nova → URG → AAES → Nexus."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from nova.bridges import law_ledger_bridge, panel_store
from nova.bridges.panel_store import PanelStore
from src.aaes_os.nexus_execution_ledger import NexusExecutionLedger, reset_nexus_execution_ledger
from src.cori.evidence_factory import reset_evidence_factory
from src.continuity.continuity_store import ContinuityStore, reset_continuity_store
from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger
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
        mission_tenant_id="tenant:acme",
        aais_instance_id="aais-local-1",
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


def test_make_governed_mission_in_process(governed_runtime: GovernedRuntimeConfig) -> None:
    trace = make_governed_mission(
        "Run governed mission test.",
        {"operator_id": "operator-test", "steward_id": "steward-test"},
        config=governed_runtime,
    )

    assert "law_eval" in trace
    assert "urg_receipt" in trace
    assert "aaes_receipt" in trace
    assert "nexus_event" in trace
    assert trace["law_eval"]["status"] == "ok"
    assert trace["urg_receipt"]["mission_id"]
    assert trace["aaes_receipt"]["status"] == "executed"
    assert trace["nexus_event"]["event_type"] == "execution"
    assert trace["constitutional_trace"]["panels"]["steward"] >= 1
    assert trace["constitutional_trace"]["references"]["ref_hash"]
    persistence = trace["constitutional_trace"]["persistence"]
    assert persistence["continuity_events"] >= 10
    assert persistence.get("evidence_events", 0) >= 6
    assert persistence["identity_snapshots"] >= 1
    assert persistence["panels"]["unified"] >= 1


def test_governed_mission_http_endpoint(governed_runtime: GovernedRuntimeConfig) -> None:
    import app.main as app_main

    client = TestClient(app_main.app)
    response = client.post(
        "/governed/mission",
        json={"text": "Run governed mission test.", "operator_id": "operator-test"},
    )
    assert response.status_code == 200, response.text
    trace = response.json()

    assert trace["law_eval"]["status"] == "ok"
    assert trace["urg_receipt"]["mission_id"]
    assert trace["aaes_receipt"]["status"] == "executed"
    assert trace["nexus_event"]["event_type"] == "execution"

    executions = client.get("/api/nexus/executions").json()
    assert executions["executions"]
    assert executions["executions"][0]["mission_id"] == trace["urg_receipt"]["mission_id"]
