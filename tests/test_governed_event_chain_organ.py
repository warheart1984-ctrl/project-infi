"""Tests for governed_event_chain_organ."""

from __future__ import annotations

from src.governed_event_chain_organ import build_governed_event_chain_status


def test_build_status():
    status = build_governed_event_chain_status()
    assert status["governed_event_chain_organ_version"] == "governed_event_chain_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
