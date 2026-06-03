"""Tests for v10_action_engine_organ."""

from __future__ import annotations

from src.v10_action_engine_organ import build_v10_action_engine_status


def test_build_status():
    status = build_v10_action_engine_status()
    assert status["v10_action_engine_organ_version"] == "v10_action_engine_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
