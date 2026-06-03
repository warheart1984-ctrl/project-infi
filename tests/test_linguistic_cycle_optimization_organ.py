"""Tests for linguistic_cycle_optimization_organ."""

from __future__ import annotations

from src.linguistic_cycle_optimization_organ import build_linguistic_cycle_optimization_status


def test_build_status():
    status = build_linguistic_cycle_optimization_status()
    assert status["linguistic_cycle_optimization_organ_version"] == "linguistic_cycle_optimization_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
