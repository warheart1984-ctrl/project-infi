"""Tests for chat_turn_governance_organ."""

from __future__ import annotations

from src.chat_turn_governance_organ import build_chat_turn_governance_status


def test_build_status():
    status = build_chat_turn_governance_status()
    assert status["chat_turn_governance_organ_version"] == "chat_turn_governance_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

