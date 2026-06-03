"""Tests for slingshot_organ."""

from __future__ import annotations

from src.slingshot_organ import build_slingshot_status


def test_build_status():
    status = build_slingshot_status()
    assert status["slingshot_organ_version"] == "slingshot_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("ma13_enforced") is True

