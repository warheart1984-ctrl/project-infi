"""Tests for v10_core_organ."""

from __future__ import annotations

from src.v10_core_organ import build_v10_core_status


def test_build_status():
    status = build_v10_core_status()
    assert status["v10_core_organ_version"] == "v10_core_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
