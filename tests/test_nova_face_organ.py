"""Tests for nova_face_organ."""

from __future__ import annotations

from src.nova_face_organ import build_nova_face_status


def test_build_status():
    status = build_nova_face_status()
    assert status["nova_face_organ_version"] == "nova_face_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

    assert status.get("authority_lane") == "jarvis"

