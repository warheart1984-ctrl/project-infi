"""MCP tool gateway — intentionally missing constraint metadata."""

from __future__ import annotations


def invoke_mcp_tool(name: str, payload: str) -> str:
    return f"mcp:{name}:{payload}"
