"""Tests for operator_profile_organ."""

from __future__ import annotations

from src.operator_profile_organ import build_operator_profile


def test_build_operator_profile_defaults():
    profile = build_operator_profile()
    assert profile["operator_profile_organ_version"] == "operator_profile_organ.v1"
    assert profile["profile_id"] == "operator"
    assert profile["authority_lane"] == "operator"
    assert "memory" in profile["capabilities"]
