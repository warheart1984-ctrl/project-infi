"""Tests for api_gateway_organ."""

from __future__ import annotations

from src.api_gateway_organ import build_api_gateway_status


def test_build_status():
    status = build_api_gateway_status()
    assert status["api_gateway_organ_version"] == "api_gateway_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

