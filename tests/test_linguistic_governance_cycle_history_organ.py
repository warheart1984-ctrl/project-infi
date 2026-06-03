"""Tests for linguistic_governance_cycle_history_organ."""

from __future__ import annotations

from src.linguistic_governance_cycle_history_organ import build_linguistic_governance_cycle_history_status


def test_build_status():
    status = build_linguistic_governance_cycle_history_status()
    assert status["linguistic_governance_cycle_history_organ_version"] == "linguistic_governance_cycle_history_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
