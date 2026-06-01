"""Deploy agent with unconstrained MCP tool access."""

from __future__ import annotations


def run_deploy(user_text: str) -> str:
    # mcp gateway reference — no allowed_actions metadata in genome
    from tools.mcp_gateway import invoke_mcp_tool

    return str(invoke_mcp_tool("deploy", user_text))
