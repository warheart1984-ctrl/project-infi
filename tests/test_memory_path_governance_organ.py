"""Tests for memory_path_governance_organ."""

from __future__ import annotations

from src.memory_path_governance_organ import build_memory_path_governance_status


def test_build_status():
    status = build_memory_path_governance_status()
    assert status["memory_path_governance_organ_version"] == "memory_path_governance_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
