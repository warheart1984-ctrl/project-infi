"""Tests for prompt_assembly_organ."""

from __future__ import annotations

from src.prompt_assembly_organ import build_prompt_assembly_status


def test_build_status():
    status = build_prompt_assembly_status()
    assert status["prompt_assembly_organ_version"] == "prompt_assembly_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]

