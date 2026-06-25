"""Workspace tool registry and JSON Schema export for lawful brain."""

from __future__ import annotations

from typing import Any, Callable

from operator_kernel.contracts import TaskConstraints

ToolHandler = Callable[..., dict[str, Any]]


def tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": "list_files",
            "description": "List files under workspace matching an optional glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob relative to workspace root", "default": "**/*"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
                },
            },
        },
        {
            "name": "read_file",
            "description": "Read a UTF-8 text file; optional line span.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "minimum": 1},
                    "end_line": {"type": "integer", "minimum": 1},
                },
                "required": ["path"],
            },
        },
        {
            "name": "search_code",
            "description": "Search code in workspace (ripgrep or Python fallback).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                },
                "required": ["query"],
            },
        },
        {
            "name": "write_patch",
            "description": "Apply a unified diff to a file under workspace root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "diff": {"type": "string"},
                },
                "required": ["path", "diff"],
            },
        },
        {
            "name": "run_command",
            "description": "Run an allowlisted shell command in workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "allowlist_id": {"type": "string"},
                },
                "required": ["command"],
            },
        },
        {
            "name": "run_tests",
            "description": "Run pytest in workspace (allowlisted).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Optional pytest target path"},
                },
            },
        },
        {
            "name": "git_status",
            "description": "Return git status --short --branch.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "git_diff",
            "description": "Return git diff for workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Optional file path"},
                },
            },
        },
        {
            "name": "git_commit",
            "description": "Create a git commit with a message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
        },
    ]


def build_registry(handlers: dict[str, ToolHandler]) -> dict[str, ToolHandler]:
    allowed = {schema["name"] for schema in tool_schemas()}
    unknown = set(handlers) - allowed
    if unknown:
        raise ValueError(f"Unknown tool handlers: {sorted(unknown)}")
    return handlers


def filter_tools_for_constraints(constraints: TaskConstraints) -> list[dict[str, Any]]:
    schemas = tool_schemas()
    if constraints.read_only:
        return [s for s in schemas if s["name"] in {"list_files", "read_file", "search_code", "git_status", "git_diff"}]
    blocked: set[str] = set()
    if not constraints.allow_shell:
        blocked.update({"run_command", "run_tests"})
    if not constraints.allow_git_commit:
        blocked.add("git_commit")
    return [s for s in schemas if s["name"] not in blocked]
