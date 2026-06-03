"""Tests for run_ledger_organ."""

from __future__ import annotations

from src.run_ledger_organ import build_run_ledger_status


def test_build_status():
    status = build_run_ledger_status()
    assert status["run_ledger_organ_version"] == "run_ledger_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
