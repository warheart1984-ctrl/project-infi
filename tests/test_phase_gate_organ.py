"""Tests for phase_gate_organ."""

from __future__ import annotations

from src.phase_gate_organ import MODULE_ID, build_phase_gate_status


def test_build_phase_gate_status():
    status = build_phase_gate_status()
    assert status["phase_gate_organ_version"] == "phase_gate_organ.v1"
    assert status["module_id"] == MODULE_ID
    assert status["registered_count"] >= 0
    assert isinstance(status["phase_histogram"], dict)
    assert status["read_only"] is True
