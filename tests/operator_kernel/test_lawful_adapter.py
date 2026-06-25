"""Lawful brain adapter parsing and frontier planner tests."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from operator_kernel.contracts import LawfulAskRequest, TaskConstraints, ToolCall
from operator_kernel.lawful_brain.adapter import (
    LawfulBrainAdapter,
    _extract_json_object,
    _parse_tool_calls,
    _tool_results_to_calls,
)
from operator_kernel.tools.openai_tools import registry_schema_to_openai_tool, schemas_to_openai_tools


def test_extract_json_from_codeblock() -> None:
    text = '```json\n{"tool_calls": [], "steps": ["a"]}\n```'
    parsed = _extract_json_object(text)
    assert parsed.get("steps") == ["a"]


def test_parse_tool_calls() -> None:
    raw = [{"id": "tc-1", "name": "list_files", "args": {"pattern": "*.py"}}]
    calls = _parse_tool_calls(raw)
    assert len(calls) == 1
    assert calls[0].name == "list_files"


def test_filter_read_only_in_request_constraints() -> None:
    req = LawfulAskRequest(
        intent="list files",
        context={},
        tools=[{"name": "write_patch"}],
        constraints=TaskConstraints(read_only=True).model_dump(),
    )
    assert req.constraints.get("read_only") is True


def test_registry_to_openai_tools() -> None:
    schema = {
        "name": "read_file",
        "description": "Read a file",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    }
    tool = registry_schema_to_openai_tool(schema)
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "read_file"
    assert len(schemas_to_openai_tools([schema])) == 1


def test_tool_results_to_calls() -> None:
    item = SimpleNamespace(id="call-1", name="read_file", arguments={"path": "foo.py"})
    calls = _tool_results_to_calls([item])
    assert calls[0].name == "read_file"
    assert calls[0].args == {"path": "foo.py"}


def test_planner_read_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_FRONTIER_PLANNER", "1")
    turn = SimpleNamespace(
        text="Reading file",
        nova_cortex={
            "tool_calls": [
                SimpleNamespace(id="tc-1", name="read_file", arguments={"path": "README.md"}),
            ]
        },
        receipt=None,
        voss_runtime={},
    )
    adapter = LawfulBrainAdapter()
    mock_llm = MagicMock()
    mock_llm.complete_openai.return_value = turn
    mock_llm.verify_receipt.return_value = True
    adapter._llm = mock_llm

    with patch("operator_kernel.lawful_brain.adapter._frontier_planner_enabled", return_value=True):
        response = adapter.ask(
            LawfulAskRequest(
                intent="read README.md",
                context={},
                tools=[{"name": "read_file", "description": "read"}],
                constraints={},
            )
        )

    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "read_file"
    assert response.tool_calls[0].args["path"] == "README.md"
    mock_llm.complete_openai.assert_called_once()


def test_planner_patch_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_FRONTIER_PLANNER", "1")
    turn = SimpleNamespace(
        text="",
        nova_cortex={
            "tool_calls": [
                SimpleNamespace(id="tc-1", name="read_file", arguments={"path": "app.py"}),
                SimpleNamespace(
                    id="tc-2",
                    name="write_patch",
                    arguments={"path": "app.py", "diff": "--- a/app.py\n+++ b/app.py\n"},
                ),
            ]
        },
        receipt=None,
        voss_runtime={},
    )
    adapter = LawfulBrainAdapter()
    mock_llm = MagicMock()
    mock_llm.complete_openai.return_value = turn
    adapter._llm = mock_llm

    with patch("operator_kernel.lawful_brain.adapter._frontier_planner_enabled", return_value=True):
        response = adapter.ask(
            LawfulAskRequest(
                intent="fix app.py",
                context={},
                tools=[
                    {"name": "read_file", "description": "read"},
                    {"name": "write_patch", "description": "patch"},
                ],
                constraints={},
            )
        )

    names = [tc.name for tc in response.tool_calls]
    assert names == ["read_file", "write_patch"]


def test_planner_run_command(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_FRONTIER_PLANNER", "1")
    turn = SimpleNamespace(
        text="",
        nova_cortex={
            "tool_calls": [
                SimpleNamespace(id="tc-1", name="run_command", arguments={"command": "pytest -q"}),
            ]
        },
        receipt=None,
        voss_runtime={},
    )
    adapter = LawfulBrainAdapter()
    mock_llm = MagicMock()
    mock_llm.complete_openai.return_value = turn
    adapter._llm = mock_llm

    with patch("operator_kernel.lawful_brain.adapter._frontier_planner_enabled", return_value=True):
        response = adapter.ask(
            LawfulAskRequest(
                intent="run tests",
                context={},
                tools=[{"name": "run_command", "description": "shell"}],
                constraints={},
            )
        )

    assert response.tool_calls[0].name == "run_command"


def test_fallback_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_FRONTIER_PLANNER", "0")
    adapter = LawfulBrainAdapter()
    mock_llm = MagicMock()
    mock_llm.ask.return_value = SimpleNamespace(
        text='{"tool_calls": [{"id": "tc-1", "name": "list_files", "args": {}}], "steps": [], "explanations": []}'
    )
    adapter._llm = mock_llm

    with patch("operator_kernel.lawful_brain.adapter._frontier_planner_enabled", return_value=False):
        response = adapter.ask(
            LawfulAskRequest(
                intent="list files",
                context={},
                tools=[{"name": "list_files", "description": "list"}],
                constraints={},
            )
        )

    mock_llm.ask.assert_called_once()
    mock_llm.complete_openai.assert_not_called()
    assert response.tool_calls[0].name == "list_files"


def test_no_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPERATOR_FRONTIER_PLANNER", "1")
    turn = SimpleNamespace(
        text="Task is already complete.",
        nova_cortex={"tool_calls": []},
        receipt=None,
        voss_runtime={},
    )
    adapter = LawfulBrainAdapter()
    mock_llm = MagicMock()
    mock_llm.complete_openai.return_value = turn
    adapter._llm = mock_llm

    with patch("operator_kernel.lawful_brain.adapter._frontier_planner_enabled", return_value=True):
        response = adapter.ask(
            LawfulAskRequest(
                intent="summarize status",
                context={},
                tools=[{"name": "list_files", "description": "list"}],
                constraints={},
            )
        )

    assert response.tool_calls == []
    assert "Task is already complete." in response.explanations[0]
