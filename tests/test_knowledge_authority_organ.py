"""Tests for knowledge_authority_organ."""

from __future__ import annotations

from src.knowledge_authority_organ import build_knowledge_authority_status


def test_build_status():
    status = build_knowledge_authority_status()
    assert status["knowledge_authority_organ_version"] == "knowledge_authority_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
