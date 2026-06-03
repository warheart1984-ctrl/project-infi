"""Tests for reasoning_contract_organ."""

from __future__ import annotations

from src.reasoning_contract_organ import build_reasoning_contract_status


def test_build_status():
    status = build_reasoning_contract_status()
    assert status["reasoning_contract_organ_version"] == "reasoning_contract_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("executive_usurpation") is False

