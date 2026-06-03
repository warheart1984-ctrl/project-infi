"""Tests for evolve_engine_organ."""

from __future__ import annotations

from src.evolve_engine_organ import build_evolve_engine_status


def test_build_status():
    status = build_evolve_engine_status()
    assert status["evolve_engine_organ_version"] == "evolve_engine_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("direct_patch_authority") is False
    assert status.get("special_review_only") is True

