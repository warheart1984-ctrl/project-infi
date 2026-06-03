"""Tests for ai_factory_organ."""

from __future__ import annotations

from src.ai_factory_organ import build_ai_factory_status


def test_build_status():
    status = build_ai_factory_status()
    assert status["ai_factory_organ_version"] == "ai_factory_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("deploy_authority_via_organ") is False

