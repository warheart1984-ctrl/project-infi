"""Tests for document_vision_organ."""

from __future__ import annotations

from src.document_vision_organ import build_document_vision_status


def test_build_status():
    status = build_document_vision_status()
    assert status["document_vision_organ_version"] == "document_vision_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert "document_vision_enabled" in status
    assert status.get("bridge_safe") is True

