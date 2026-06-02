"""Tests for safety_envelope_organ."""

from __future__ import annotations

from pathlib import Path

from src.safety_envelope import build_envelope_status


def test_build_envelope_status():
    status = build_envelope_status(root=Path(__file__).resolve().parents[1])
    assert status["safety_envelope_organ_version"] == "safety_envelope_organ.v1"
    assert status["envelope_id"] == "default"
    assert "thresholds" in status
    assert status["read_only"] is True
