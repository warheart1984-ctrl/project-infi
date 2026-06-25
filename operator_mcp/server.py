"""MCP stdio server that proxies OperatorKernel REST endpoints."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "operator_mcp requires the 'mcp' package. Install with: pip install mcp httpx"
    ) from exc

DEFAULT_KERNEL_URL = "http://127.0.0.1:8790"
KERNEL_URL = os.environ.get("OPERATOR_KERNEL_URL", DEFAULT_KERNEL_URL).rstrip("/")

mcp = FastMCP(
    "operator-kernel",
    instructions=(
        "Proxies a running OperatorKernel agent API. Start Operator Desktop or "
        "`python -m operator_kernel` before calling tools. Set OPERATOR_KERNEL_URL "
        "if the kernel is not on 127.0.0.1:8790."
    ),
)


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


async def _get(path: str) -> Any:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{KERNEL_URL}{path}")
        response.raise_for_status()
        return response.json()


async def _post(path: str, body: dict[str, Any] | None = None) -> Any:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(f"{KERNEL_URL}{path}", json=body or {})
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def operator_health() -> str:
    """Check kernel health and lawful-brain reachability."""
    return _json(await _get("/health"))


@mcp.tool()
async def operator_list_tasks() -> str:
    """List agent tasks (newest first)."""
    return _json(await _get("/agent/tasks"))


@mcp.tool()
async def operator_get_task(task_id: str) -> str:
    """Fetch task metadata and full event log by task_id."""
    return _json(await _get(f"/agent/tasks/{task_id}"))


@mcp.tool()
async def operator_create_task(
    goal: str,
    workspace_root: str | None = None,
    agent_id: str | None = None,
    title: str | None = None,
    read_only: bool = False,
    allow_shell: bool = False,
    allow_git_commit: bool = False,
    allow_network: bool = False,
    max_steps: int = 12,
) -> str:
    """Create and start an agent task. Returns task_id and initial status."""
    body: dict[str, Any] = {
        "goal": goal,
        "constraints": {
            "read_only": read_only,
            "allow_shell": allow_shell,
            "allow_git_commit": allow_git_commit,
            "allow_network": allow_network,
            "max_steps": max(1, min(50, max_steps)),
        },
    }
    if workspace_root:
        body["workspace_root"] = workspace_root
    if agent_id:
        body["agent_id"] = agent_id
    if title:
        body["title"] = title
    return _json(await _post("/agent/tasks", body))


@mcp.tool()
async def operator_cancel_task(task_id: str) -> str:
    """Request cooperative cancellation of a running task."""
    return _json(await _post(f"/agent/tasks/{task_id}/cancel"))


@mcp.tool()
async def operator_append_message(task_id: str, text: str) -> str:
    """Append a user message to an existing task (continues the agent loop)."""
    return _json(await _post(f"/agent/tasks/{task_id}/message", {"text": text}))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
