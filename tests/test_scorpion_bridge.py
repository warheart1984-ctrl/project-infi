"""Tests for scorpion_bridge."""

from __future__ import annotations

from src.scorpion_bridge import bridge_status


def test_bridge_status_shape():
    status = bridge_status()
    assert status["bridge_version"] == "scorpion_bridge.v1"
    assert status["read_only"] is True
    assert "scorpion_status" in status
