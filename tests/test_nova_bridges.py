"""Tests for nova/bridges adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from nova.bridges import boundary_bridge, cockpit_bridge, law_ledger_bridge, panel_store
from nova.bridges.panel_store import PanelStore
from nova.crk.lineage.reflexive_events import clear_reflexive_events, emit_reflexive_eval, list_reflexive_events
from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.models import LawStatus, new_law_record
from nova.law_kernel.types import LawEvent


@pytest.fixture()
def law_ledger_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "law-ledger.sqlite3"
    monkeypatch.setenv("LAW_LEDGER_PATH", str(path))
    from src.continuity.law_ledger import LawLedgerStore, bootstrap_law_ledger

    store = LawLedgerStore(path=path)
    bootstrap_law_ledger(store)
    law_ledger_bridge.reset_law_ledger_store(store)
    yield store
    law_ledger_bridge.reset_law_ledger_store(None)


@pytest.fixture()
def panel_store_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "panels.sqlite3"
    store = PanelStore(path=path)
    panel_store.reset_panel_store(store)
    monkeypatch.setenv("NOVA_PANEL_STORE_PATH", str(path))
    yield store
    panel_store.reset_panel_store(None)
    clear_reflexive_events()


def test_boundary_bridge_maps_kernel_snapshot():
    summary = boundary_bridge.compute_boundary_status("agent:test")
    assert summary["status"] in {"stable", "warning", "violation"}
    assert "insufficiency" in summary["details"] or summary["details"].startswith("focus=")
    panel = boundary_bridge.to_panel_status(summary, epoch_id="EPOCH:1:T0")
    assert panel["epoch_id"] == "EPOCH:1:T0"
    assert panel["status"] == summary["status"]


def test_law_ledger_bridge_round_trip(law_ledger_path):
    event = LawEvent(
        entry_type="LAW_EVAL",
        law_id="PIT-1",
        law_hash="hash-pit-1",
        epoch=2,
        payload={"fitness": 0.91},
        signed_by="test",
    )
    law_ledger_bridge.record_law_event(event)
    latest = law_ledger_bridge.get_latest_law_snapshot("PIT-1")
    assert latest is not None
    assert latest.code == "PIT-1"
    history = list(law_ledger_bridge.get_law_history("PIT-1"))
    assert history


def test_cockpit_bridge_from_legacy_shape():
    legacy = {
        "epoch": 3,
        "boundary_detection": {"insufficiency": 0.1, "signals": [0.1, 0.2, 0.0, 0.0, 0.0]},
        "reference_integrity": {"reference_integrity": 0.95},
        "sovereign_laws": [{"law_id": "PIT-1"}],
    }
    summary = cockpit_bridge.CockpitSummaryV2.from_legacy(legacy)
    body = summary.to_dict()
    assert body["boundary_detection"]["status"] == "stable"
    assert body["pit_evolution"]["epoch_id"] == "EPOCH:3:T0"


def test_law_ledger_persist_round_trip(law_ledger_path):
    ledger = LawLedger(persist=True)
    record = new_law_record(
        code="PIT-TEST",
        text="test law",
        status=LawStatus.ADMITTED,
        fitness=0.9,
        epoch="EPOCH:1:T0",
    )
    ledger.append(record)

    reloaded = LawLedger(persist=True)
    assert reloaded.get("PIT-TEST") is not None
    assert reloaded.get("PIT-TEST").fitness == 0.9


def test_panel_store_reflexive_persistence(panel_store_path):
    clear_reflexive_events()
    emit_reflexive_eval(
        epoch_id="EPOCH:9:T0",
        intent_id="intent-1",
        lineage_event_id="le-1",
        t5_ref_signal_hash="ref-panel",
        report={"reflexive_health": "good"},
    )
    assert len(list_reflexive_events()) == 1

    import nova.crk.lineage.reflexive_events as reflexive_mod

    reflexive_mod._events.clear()
    reflexive_mod._hydrated = False
    assert len(list_reflexive_events()) == 1
