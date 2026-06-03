"""Tests for OTEM capability level configuration."""

from __future__ import annotations

import os

from src.otem_capability import (
    OTEM_DEFAULT_CAPABILITY_LEVEL,
    allows_execution_approval_path,
    get_otem_capability_level,
    get_otem_version_ceiling,
    max_plan_steps,
)


def test_default_capability_level_is_10():
    os.environ.pop("AAIS_OTEM_CAPABILITY_LEVEL", None)
    assert get_otem_capability_level() == OTEM_DEFAULT_CAPABILITY_LEVEL == 10
    assert get_otem_version_ceiling() == "v10_governed"
    assert allows_execution_approval_path() is True
    assert max_plan_steps() == 10


def test_level_5_keeps_v5_frozen_posture(monkeypatch):
    monkeypatch.setenv("AAIS_OTEM_CAPABILITY_LEVEL", "5")
    assert get_otem_capability_level() == 5
    assert get_otem_version_ceiling() == "v5_frozen"
    assert allows_execution_approval_path() is False
    assert max_plan_steps() == 5
