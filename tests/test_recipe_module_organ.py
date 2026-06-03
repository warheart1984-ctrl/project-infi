"""Tests for recipe_module_organ."""

from __future__ import annotations

from src.recipe_module_organ import build_recipe_module_status


def test_build_status():
    status = build_recipe_module_status()
    assert status["recipe_module_organ_version"] == "recipe_module_organ.v1"
    assert status["read_only"] is True
    assert status["module_id"]
