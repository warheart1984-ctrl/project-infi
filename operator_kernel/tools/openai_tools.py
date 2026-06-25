"""Convert operator tool registry schemas to OpenAI function tool format."""

from __future__ import annotations

from typing import Any

from operator_kernel.contracts import TaskConstraints
from operator_kernel.tools.registry import filter_tools_for_constraints, tool_schemas


def registry_schema_to_openai_tool(schema: dict[str, Any]) -> dict[str, Any]:
    """Map flat registry schema to OpenAI tools API shape."""
    return {
        "type": "function",
        "function": {
            "name": str(schema["name"]),
            "description": str(schema.get("description") or ""),
            "parameters": schema.get("parameters") or {"type": "object", "properties": {}},
        },
    }


def schemas_to_openai_tools(schemas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [registry_schema_to_openai_tool(schema) for schema in schemas]


def openai_tools_for_constraints(constraints: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Filter registry tools by task constraints and return OpenAI tool definitions."""
    if not constraints:
        return schemas_to_openai_tools(tool_schemas())
    model = TaskConstraints(**constraints)
    filtered = filter_tools_for_constraints(model)
    return schemas_to_openai_tools(filtered)
