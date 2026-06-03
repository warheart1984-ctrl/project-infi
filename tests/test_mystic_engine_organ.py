"""Tests for mystic_engine_organ."""

from __future__ import annotations

from src.mystic_engine_organ import build_mystic_engine_status


def test_build_status():
    status = build_mystic_engine_status()
    assert status["mystic_engine_organ_version"] == "mystic_engine_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

