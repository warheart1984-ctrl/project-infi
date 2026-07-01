from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from nova.node.continuity import read_events
from nova.node.event_bus import read_event_history
from nova.node.feature_manifest import feature_manifest
from nova.node.ledger import stable_hash
from nova.node.policy import load_node_policy
from nova.node.tools import replay_coding


router = APIRouter()

COMPARE_KEYS = ["receipt_hash", "input_hash", "output_hash", "policy_version", "tool", "intent"]


@router.get("/node/verify/{trace_id}")
async def verify_trace(trace_id: str) -> dict[str, Any]:
    receipt = _load_tool_receipt(trace_id)
    replay = _replay_verification(trace_id, receipt)
    return {
        "trace_id": trace_id,
        "receipt": receipt,
        "verification": {
            "receipt_hash": _check_hash(receipt, _receipt_material(receipt), "receipt_hash"),
            "input_hash": _check_hash(receipt, receipt.get("input_snapshot"), "input_hash"),
            "output_hash": _check_hash(receipt, receipt.get("output_snapshot"), "output_hash"),
            "original_code_hash": _check_hash(receipt, receipt.get("current_code", ""), "original_code_hash"),
            "replay": replay,
        },
        "policy": _policy_evidence(receipt),
        "trace": trace_evidence(trace_id),
        "cross_node": {
            "comparable": True,
            "compare_keys": COMPARE_KEYS,
        },
    }


@router.get("/node/trace/{trace_id}")
async def get_trace(trace_id: str) -> dict[str, Any]:
    return {"trace_id": trace_id, **trace_evidence(trace_id)}


@router.post("/node/compare-receipts")
async def compare_receipts(request: Request) -> dict[str, Any]:
    payload = await request.json()
    left = payload.get("left") or {}
    right = payload.get("right") or {}
    matches = {
        key: left.get(key) == right.get(key)
        for key in COMPARE_KEYS
        if key in left or key in right
    }
    drift_keys = [key for key, matched in matches.items() if not matched]
    return {
        "matching": not drift_keys,
        "matches": matches,
        "drift_keys": drift_keys,
        "compare_keys": COMPARE_KEYS,
    }


def trace_evidence(trace_id: str) -> dict[str, Any]:
    return {
        "events": [
            event for event in read_event_history()
            if (event.get("payload") or {}).get("trace_id") == trace_id
        ],
        "continuity": [
            _normalize_continuity_event(event) for event in read_events()
            if event.get("trace_id") == trace_id or (event.get("data") or {}).get("trace_id") == trace_id
        ],
    }


def _load_tool_receipt(trace_id: str) -> dict[str, Any]:
    try:
        return replay_coding.load_receipt(trace_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="trace receipt not found") from exc


def _receipt_material(receipt: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in receipt.items() if key != "receipt_hash"}


def _check_hash(receipt: dict[str, Any], material: Any, field: str) -> dict[str, Any]:
    expected = receipt.get(field)
    actual = stable_hash(material) if material is not None else None
    return {
        "expected": expected,
        "actual": actual,
        "valid": bool(expected and actual and expected == actual),
    }


def _replay_verification(trace_id: str, receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("intent") != "code":
        return {"available": False, "reason": "replay currently supports code receipts"}
    try:
        replayed = replay_coding.replay_coding(trace_id)
    except Exception as exc:
        return {"available": False, "reason": str(exc)}
    return {
        "available": True,
        "deterministic": bool(replayed.get("deterministic")),
        "policy_version": replayed.get("policy_version"),
        "diff_against_original": replayed.get("diff_against_original"),
    }


def _policy_evidence(receipt: dict[str, Any]) -> dict[str, Any]:
    policy = load_node_policy()
    return {
        "version": receipt.get("policy_version") or policy.get("policy_version"),
        "current_version": policy.get("policy_version"),
        "policy_hash": policy.get("policy_hash"),
        "manifest": feature_manifest(),
    }


def _normalize_continuity_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        **event,
        "kind": event.get("kind") or event.get("entry_type") or "continuity",
    }
