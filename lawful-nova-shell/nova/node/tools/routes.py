from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from nova.node.event_bus import get_event_bus
from nova.node.ledger import stable_hash
from nova.node.policy import GovernanceRuntime
from nova.node.runtime_hooks import RuntimeHooks
from nova.node.tools.receipts import write_coding_receipt
from nova.node.tools.replay_coding import load_receipt
from nova.node.tools.registry import TOOLS, UnknownToolIntent, invoke_tool

router = APIRouter()


@router.get("/node/tools")
async def node_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": name,
                "profile": str(entry["profile"]),
                "capabilities": list(entry["capabilities"]),
                "stateless": True,
                "owner_agent": str(entry["owner_agent"]),
                "tool_manifest_name": str(entry["tool_manifest_name"]),
                "description": _tool_description(name),
            }
            for name, entry in TOOLS.items()
        ]
    }


@router.post("/node/tool")
async def node_tool(request: Request) -> Any:
    payload = await request.json()
    hooks = RuntimeHooks(get_event_bus())
    governance = GovernanceRuntime().enforce_invariants(payload)
    if governance["decision"] != "allowed":
        hooks.on_receipt_blocked(governance)
        return JSONResponse({"error": governance}, status_code=400)

    intent = str(payload.get("intent") or "")
    trace_id = str(governance["trace_id"])
    start = time.perf_counter()
    hooks.on_tool_invoked(
        intent,
        stable_hash(payload),
        str(governance.get("decision")),
        trace_id,
    )
    try:
        result = invoke_tool(intent, payload)
    except UnknownToolIntent:
        hooks.on_receipt_blocked(
            {
                **governance,
                "tool_name": intent,
                "reason": "unknown-tool-intent",
            }
        )
        return JSONResponse(
            {
                "error": {
                    "decision": "blocked",
                    "reason": "unknown-tool-intent",
                    "policy_version": governance.get("policy_version"),
                }
            },
            status_code=400,
        )

    trace_file = write_coding_receipt(
        trace_id=trace_id,
        task=payload,
        governance=governance,
        result=result,
        tool=intent,
    )
    duration_ms = int((time.perf_counter() - start) * 1000)
    if result.get("diff"):
        hooks.on_patch_generated(trace_id, str(result.get("file_path") or ""), stable_hash(result["diff"]))
    hooks.on_tool_completed(intent, stable_hash(result), duration_ms, trace_id)
    hooks.on_receipt_verified(
        {
            **governance,
            "tool_name": intent,
            "receipt_hash": stable_hash({"trace_file": trace_file, "result": result}),
        }
    )
    return {
        "result": result,
        "governance": governance,
        "receipt": load_receipt(trace_id),
        "trace_file": trace_file,
    }


def _tool_description(name: str) -> str:
    if name == "code":
        return "Stateless Ring-2 coder tool returning updated code and unified diff."
    if name == "wire":
        return "Stateless Ring-2 wiring tool returning glue code, routes, manifests, and config."
    if name == "explain":
        return "Stateless Ring-2 explanation tool returning patch rationale, risk, and test guidance."
    return "Stateless governed Node tool."
