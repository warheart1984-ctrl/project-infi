"""Continuity SDK v0 — public import surface."""

from __future__ import annotations

import importlib


def test_continuity_sdk_public_imports() -> None:
  sdk = importlib.import_module("continuity_sdk")
  assert hasattr(sdk, "LawfulLLMAdapter")
  assert hasattr(sdk, "FallingObjectModel")
  assert hasattr(sdk, "run_falling_object_scenario")
  assert hasattr(sdk, "run_mission_005_calibration_lineage_stress")


def test_mvcd_demo() -> None:
  from continuity_sdk import run_falling_object_scenario

  correction, crr1 = run_falling_object_scenario()
  assert correction.model_shift.magnitude > 0
  assert crr1["calibration_delta"] != 0


def test_mission_005_demo() -> None:
  from continuity_sdk import run_mission_005_calibration_lineage_stress

  report = run_mission_005_calibration_lineage_stress()
  assert report.passed


def test_branding_assets() -> None:
  from continuity_sdk.branding import (
    SDK_BADGE,
    SDK_BADGE_SMALL,
    SDK_SIGIL,
    STEWARD_ONBOARDING,
    steward_onboarding_path,
  )

  assert "CONTINUITY SDK" in SDK_BADGE
  assert "v1" in SDK_BADGE_SMALL
  assert "REALITY ROOTS" in SDK_SIGIL
  assert "STEWARD ONBOARDING" in STEWARD_ONBOARDING
  assert steward_onboarding_path().is_file()


def test_cli_info_and_onboarding(capsys) -> None:
  from continuity_sdk.cli import cmd_info, cmd_onboarding

  assert cmd_info() == 0
  info_out = capsys.readouterr().out
  assert "K‑∞" in info_out or "K-∞" in info_out

  assert cmd_onboarding() == 0
  onboarding_out = capsys.readouterr().out
  assert "lawful steward" in onboarding_out
