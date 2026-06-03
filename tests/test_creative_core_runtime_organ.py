"""Tests for creative_core_runtime_organ."""

from __future__ import annotations

from src.creative_core_runtime_organ import build_creative_core_runtime_status


def test_build_status():
    status = build_creative_core_runtime_status()
    assert status["creative_core_runtime_organ_version"] == "creative_core_runtime_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
