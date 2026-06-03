"""Tests for aais_doctor_organ."""

from __future__ import annotations

from src.aais_doctor_organ import build_aais_doctor_status


def test_build_status():
    status = build_aais_doctor_status()
    assert status["aais_doctor_organ_version"] == "aais_doctor_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

