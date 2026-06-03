"""Tests for provider_route_organ."""

from __future__ import annotations

from src.provider_route_organ import build_provider_route_status


def test_build_status():
    status = build_provider_route_status()
    assert status["provider_route_organ_version"] == "provider_route_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("advisory_only") is True
    assert status.get("execution_allowed") is False

