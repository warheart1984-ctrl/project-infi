"""Tests for direct_challenge_organ."""

from __future__ import annotations

from src.direct_challenge_organ import build_direct_challenge_status


def test_build_status():
    status = build_direct_challenge_status()
    assert status["direct_challenge_organ_version"] == "direct_challenge_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
