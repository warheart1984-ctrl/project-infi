"""Tests for spatial_reasoning_organ."""

from __future__ import annotations

from src.spatial_reasoning_organ import build_spatial_reasoning_status


def test_build_status():
    status = build_spatial_reasoning_status()
    assert status["spatial_reasoning_organ_version"] == "spatial_reasoning_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

