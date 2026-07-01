from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from nova.config import load_nova_config
from nova.errors import ProviderError
from nova.node.continuity import append_event, append_receipt, last_receipt_hash
from nova.node.ledger import runtime_dir, stable_hash, stable_json
from nova.node.policy import GovernanceRuntime, NodeVeto, load_node_policy
from nova.providers import build_provider

router = APIRouter()


def submit_node_task(packet: dict[str, Any], provider: Any) -> dict[str, Any]:
    decision = GovernanceRuntime().enforce_invariants(packet)
    if decision["decision"] != "allowed":
        raise NodeVeto(reason=str(decision.get("reason") or "blocked"), policy_version=str(decision["policy_version"]))

    policy = load_node_policy()
    payload = packet.get("payload") or _payload_from_flat_packet(packet)
    task_id = str(packet.get("task_id") or f"task-{time.time_ns()}")
    trace_id = str(decision["trace_id"])
    append_event("submit", {"payload": packet, "decision": decision})

    governed_request = {
        "messages": _payload_messages(payload),
        "temperature": payload.get("temperature"),
        "max_tokens": payload.get("max_tokens"),
        "slice_id": task_id,
        "slice_version": "node-v0",
        "continuity_hash": stable_hash({"previous": last_receipt_hash()}),
        "governance_path": ["node.v0", "policy.veto", "provider.execute"],
    }
    provider_result = provider.chat_completion(governed_request)
    completion = provider_result["completion"]
    output = str(completion["choices"][0]["message"]["content"])
    result = {"output": output, "completion_id": completion["id"]}
    receipt = _receipt(
        policy=policy,
        packet=packet,
        task_id=task_id,
        trace_id=trace_id,
        model_id=str(completion.get("model") or getattr(provider, "model", "unknown")),
        output=result,
    )
    response = {
        "decision": "allowed",
        "trace_id": trace_id,
        "result": result,
        "receipt": receipt,
        "receipts": [receipt["receipt_hash"]],
    }
    append_receipt({
        "entry_type": "nodeExecutionReceipt",
        "trace_id": trace_id,
        "timestamp": receipt["timestamp"],
        "task_id": task_id,
        "receipt_hash": receipt["receipt_hash"],
        "receipt": receipt,
    })
    append_event("result", {"trace_id": trace_id, "completion_id": completion["id"]})
    _write_result(trace_id, response)
    return response


def load_node_result(trace_id: str) -> dict[str, Any]:
    path = _result_path(trace_id)
    if not path.exists():
        raise KeyError(trace_id)
    return json.loads(path.read_text(encoding="utf-8"))


@router.post("/node/submit")
async def node_submit(request: Request) -> Any:
    body = await request.json()
    provider_factory = getattr(request.app.state, "node_provider_factory", build_provider)
    provider = provider_factory(load_nova_config())
    try:
        return submit_node_task(body, provider)
    except NodeVeto as exc:
        return JSONResponse(
            {"error": {"decision": "blocked", "reason": exc.reason, "policy_version": exc.policy_version}},
            status_code=400,
        )
    except ProviderError as exc:
        return JSONResponse({"error": {"code": exc.code, "message": exc.message}}, status_code=500)


@router.post("/node/result")
async def node_result(request: Request) -> Any:
    body = await request.json()
    provider_factory = getattr(request.app.state, "node_provider_factory", build_provider)
    provider = provider_factory(load_nova_config())
    governed_request = body.get("payload", {})
    result = provider.chat_completion(governed_request)
    event = append_event("result", {"payload": governed_request, "completion_id": result["completion"]["id"]})
    return {"completion": result["completion"], "receipt": result["receipt"], "event_id": event["event_id"]}


@router.get("/node/result/{trace_id}")
async def node_result_by_trace(trace_id: str) -> Any:
    try:
        return load_node_result(trace_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="node result not found") from None


def _payload_from_flat_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": packet.get("messages") or [],
        "temperature": packet.get("temperature"),
        "max_tokens": packet.get("max_tokens"),
    }


def _payload_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    messages = payload.get("messages")
    if isinstance(messages, list) and messages:
        return [
            {"role": str(message.get("role") or "user"), "content": str(message.get("content") or "")}
            for message in messages
            if isinstance(message, dict)
        ]
    prompt = str(payload.get("prompt") or stable_json(payload))
    return [{"role": "user", "content": prompt}]


def _receipt(
    *,
    policy: dict[str, Any],
    packet: dict[str, Any],
    task_id: str,
    trace_id: str,
    model_id: str,
    output: dict[str, Any],
) -> dict[str, Any]:
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    body = {
        "entry_type": "nodeExecutionReceipt",
        "node_id": policy["node_id"],
        "operator_key_id": policy["operator_key_id"],
        "task_id": task_id,
        "trace_id": trace_id,
        "intent": str(packet.get("intent") or "unspecified"),
        "caller_id": str(packet.get("caller_id") or "unknown"),
        "policy_version": policy["policy_version"],
        "policy_hash": policy["policy_hash"],
        "model_id": model_id,
        "input_hash": stable_hash(packet),
        "output_hash": stable_hash(output),
        "timestamp": timestamp,
    }
    return {**body, "receipt_hash": stable_hash(body)}


def _result_path(trace_id: str) -> Path:
    return runtime_dir() / "results" / f"{trace_id}.json"


def _write_result(trace_id: str, response: dict[str, Any]) -> None:
    path = _result_path(trace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(response) + "\n", encoding="utf-8")
