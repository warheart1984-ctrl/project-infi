"""Compile workflow steps to ordered job plan."""

from __future__ import annotations

from typing import Any


def compile_steps(steps: list[dict[str, str]]) -> list[dict[str, str]]:
    plan: list[dict[str, str]] = []
    for i, step in enumerate(steps):
        subsystem = str(step.get("subsystem") or "")
        kind = str(step.get("kind") or "")
        if not subsystem or not kind:
            continue
        plan.append(
            {
                "index": str(i),
                "subsystem": subsystem,
                "kind": kind,
                "params": step.get("params") or {},
            }
        )
    return plan
