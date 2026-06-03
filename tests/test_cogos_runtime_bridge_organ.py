"""Tests for cogos_runtime_bridge_organ."""

from __future__ import annotations

from src.cogos_runtime_bridge_organ import build_cogos_runtime_bridge_status


def test_build_status():
    status = build_cogos_runtime_bridge_status()
    assert status["cogos_runtime_bridge_organ_version"] == "cogos_runtime_bridge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

