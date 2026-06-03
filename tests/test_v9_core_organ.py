"""Tests for v9_core_organ."""

from __future__ import annotations

from src.v9_core_organ import build_v9_core_status


def test_build_status():
    status = build_v9_core_status()
    assert status["v9_core_organ_version"] == "v9_core_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
