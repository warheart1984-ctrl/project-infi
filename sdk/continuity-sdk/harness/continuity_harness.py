"""Continuity experiment harness entrypoint."""

from __future__ import annotations

from typing import Any, Callable


def run_experiment(name: str, runner: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    result = runner()
    result["experiment"] = name
    result["status"] = "pass" if result.get("passed", result.get("continuity_passed", False)) else "fail"
    return result


def run_mission_006() -> dict[str, Any]:
    from .assimilation import run_assimilation_demo

    return run_experiment("mission_006_assimilation", run_assimilation_demo)
