"""Continuity mechanisms — meaning ledger, ROOT-014 freeze, early concept harness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.continuity.continuity_mechanisms import (
    ROOT_014,
    apply_continuity_mechanisms,
    run_early_concept_reconstruction,
)
from src.continuity.meaning_ledger import MeaningLedger


ROOT = Path(__file__).resolve().parents[1]


def test_early_concept_harness_passes() -> None:
    proof = run_early_concept_reconstruction()
    assert proof["passed"] is True
    assert proof["anchor_ok"] is True


def test_apply_continuity_mechanisms_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    online = tmp_path / "online"
    online.mkdir()
    monkeypatch.setenv("AAIS_ONLINE_RUNTIME_DIR", str(online))
    monkeypatch.setenv("MEANING_LEDGER_PATH", str(online / "meaning-ledger.jsonl"))
    monkeypatch.setenv("CAB_STORE", str(online / "cab-ledger.jsonl"))
    monkeypatch.setenv("TSR_ROUTING_PATH", str(online / "tsr-routing.json"))

    first = apply_continuity_mechanisms()
    second = apply_continuity_mechanisms()

    assert first["early_concept_harness"]["passed"] is True
    assert first["substrate_safe"] is True
    assert second["meaning_ledger_backfill_count"] == 0
    assert second["mechanism_entries_added"] == 0
    assert len(second["cab_decisions_added"]) == 0

    ledger = MeaningLedger()
    assert ledger.get("ML-BACKFILL-001") is not None
    assert ledger.get(ROOT_014) is not None
    assert ledger.get("ML-DRIFT-DANIEL-001") is not None

    snapshot_path = online / "continuity-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["substrate_safe"] is True
    assert snapshot["phase"] == "implementation"
    assert snapshot["root_014_active"] is True
