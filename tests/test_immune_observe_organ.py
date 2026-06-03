"""Tests for immune_observe_organ."""

from __future__ import annotations

from src.immune_observe_organ import build_immune_observe_status


def test_build_status():
    status = build_immune_observe_status()
    assert status["immune_observe_organ_version"] == "immune_observe_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
