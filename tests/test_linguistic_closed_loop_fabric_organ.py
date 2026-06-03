"""Tests for linguistic_closed_loop_fabric_organ."""

from __future__ import annotations

from src.linguistic_closed_loop_fabric_organ import build_linguistic_closed_loop_fabric_status


def test_build_status():
    status = build_linguistic_closed_loop_fabric_status()
    assert status["linguistic_closed_loop_fabric_organ_version"] == "linguistic_closed_loop_fabric_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
