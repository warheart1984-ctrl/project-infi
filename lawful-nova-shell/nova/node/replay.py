from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from nova.config import load_nova_config
from nova.errors import ProviderError
from nova.node.continuity import read_events
from nova.node.policy import NodeVeto
from nova.node.submit import load_node_result, submit_node_task
from nova.providers import build_provider

router = APIRouter()


def replay_trace(trace_id: str, provider: Any) -> dict[str, Any]:
    try:
        original = load_node_result(trace_id)
    except KeyError:
        raise ValueError(f"Unknown trace_id: {trace_id}") from None

    packet = _find_original_packet(trace_id)
    if packet is None:
        raise ValueError(f"Missing submit event for trace_id: {trace_id}")

    replayed = submit_node_task({**packet, "task_id": f"replay-{packet.get('task_id', trace_id)}"}, provider)
    original_output = original.get("result")
    replayed_output = replayed.get("result")
    diff = _compute_diff(original_output, replayed_output)
    return {
        "trace_id": trace_id,
        "replay_trace_id": replayed["trace_id"],
        "original_output": original_output,
        "replayed_output": replayed_output,
        "deterministic": diff["type"] == "none",
        "diff": diff,
        "policy_version_original": original.get("receipt", {}).get("policy_version"),
        "policy_version_replayed": replayed.get("receipt", {}).get("policy_version"),
        "governance_original": original.get("decision"),
        "governance_replayed": replayed.get("decision"),
        "replay_receipts": replayed.get("receipts", []),
    }


@router.post("/node/replay/{trace_id}")
async def replay_node_trace(trace_id: str, request: Request) -> Any:
    provider_factory = getattr(request.app.state, "node_provider_factory", build_provider)
    provider = provider_factory(load_nova_config())
    try:
        return replay_trace(trace_id, provider)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except NodeVeto as exc:
        return JSONResponse(
            {"error": {"decision": "blocked", "reason": exc.reason, "policy_version": exc.policy_version}},
            status_code=400,
        )
    except ProviderError as exc:
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=500)


def _find_original_packet(trace_id: str) -> dict[str, Any] | None:
    for event in read_events():
        if event.get("kind") != "submit":
            continue
        data = event.get("data") or {}
        decision = data.get("decision") or {}
        if decision.get("trace_id") == trace_id:
            payload = data.get("payload")
            return payload if isinstance(payload, dict) else None
    return None


def _compute_diff(original: Any, replayed: Any) -> dict[str, Any]:
    if original == replayed:
        return {"type": "none", "details": {}}
    return {"type": "structural", "details": {"original": original, "replayed": replayed}}
