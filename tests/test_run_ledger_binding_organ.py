"""Tests for run_ledger_binding_organ."""

from __future__ import annotations

from src.run_ledger_binding_organ import build_run_ledger_binding_status


def test_build_status():
    status = build_run_ledger_binding_status()
    assert status["run_ledger_binding_organ_version"] == "run_ledger_binding_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

