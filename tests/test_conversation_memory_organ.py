"""Tests for conversation_memory_organ."""

from __future__ import annotations

from src.conversation_memory_organ import build_conversation_memory_status


def test_build_status():
    status = build_conversation_memory_status()
    assert status["conversation_memory_organ_version"] == "conversation_memory_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

