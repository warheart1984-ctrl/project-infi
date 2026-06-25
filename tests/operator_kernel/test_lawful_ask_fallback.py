"""Operator kernel uses in-process lawful brain when HTTP service is down."""

from __future__ import annotations

import asyncio

from operator_kernel.agent_loop import _lawful_ask
from operator_kernel.config import OperatorKernelConfig
from operator_kernel.contracts import TaskConstraints


def test_lawful_ask_falls_back_when_brain_unreachable(monkeypatch):
    monkeypatch.setenv("AAIS_PLANNER_FALLBACK", "1")
    config = OperatorKernelConfig(
        lawful_brain_url="http://127.0.0.1:59999",
        workspace_root=".",
    )
    constraints = TaskConstraints()

    result = asyncio.run(
        _lawful_ask(
            config,
            "list files in workspace",
            {"session_id": "test"},
            [],
            constraints,
        )
    )

    assert isinstance(result, dict)
    assert "plan" in result
    assert "tool_calls" in result
    assert isinstance(result["tool_calls"], list)
