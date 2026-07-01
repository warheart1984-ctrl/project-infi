from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from nova.node.continuity import read_events
from nova.node.event_bus import read_event_history
from nova.node.ledger import read_ledger
from nova.node.policy import get_rate_limit_state, load_node_policy
from nova.node.federation import load_peers
from nova.node.consensus import policy_hash_consensus
from nova.node.alerts import list_alerts
from nova.node.mesh import get_mesh

router = APIRouter()


def node_status() -> dict[str, Any]:
    policy = load_node_policy()
    return {
        "node": "Lawful Nova Node v0",
        "node_id": policy["node_id"],
        "operator_key_id": policy["operator_key_id"],
        "policy_version": policy["policy_version"],
        "policy_hash": policy["policy_hash"],
        "conformance_profile": policy["conformance_profile"],
        "receipt_count": len([e for e in read_events() if e.get("entry_type") == "nodeExecutionReceipt"]),
        "governance_health": _governance_health(),
        "rate_limits": get_rate_limit_state(),
        "federation": _federation_state(),
        "endpoints": [
            "/v1/models",
            "/v1/chat/completions",
            "/v1/completions",
            "/node/status",
            "/node/submit",
            "/node/tool",
            "/node/tools",
            "/node/agents",
            "/node/agent-tools",
            "/node/events",
            "/node/substrate-events",
            "/node/feature-manifest",
            "/node/verify/{trace_id}",
            "/node/trace/{trace_id}",
            "/node/compare-receipts",
            "/node/result/{trace_id}",
            "/node/receipts",
            "/node/ledger",
            "/node/gossip",
            "/node/hello",
            "/node/replay/{trace_id}",
            "/node/continuity",
            "/node/policy",
            "/node/mesh",
            "/node/alerts",
            "/node/conformance/n0",
            "/node/conformance/n0/badge",
            "/node/evidence-bundle",
        ],
    }


@router.get("/node/status")
async def get_status() -> dict[str, Any]:
    return node_status()


@router.get("/node/receipts")
async def get_receipts() -> dict[str, Any]:
    return {"receipts": [e for e in read_events() if e.get("entry_type") == "nodeExecutionReceipt"]}


@router.get("/node/ledger")
async def get_ledger() -> dict[str, Any]:
    return {"ledger": read_ledger(), "continuity": read_events()}


@router.get("/node/continuity")
async def get_continuity(limit: int = 500) -> dict[str, Any]:
    events = [_flatten_continuity_event(event) for event in read_events()]
    return {"events": events[-limit:]}


def _governance_health() -> dict[str, Any]:
    ledger = read_ledger()
    continuity = read_events()
    invalid_signatures = [
        entry for entry in ledger
        if entry.get("entry_type") == "nodeGossipReceipt" and entry.get("signature_valid") is False
    ]
    return {
        "ledger_entries": len(ledger),
        "continuity_events": len(continuity),
        "event_bus_events": len(read_event_history()),
        "invalid_signatures": len(invalid_signatures),
    }


def _federation_state() -> dict[str, Any]:
    gossip = [
        entry for entry in read_ledger()
        if entry.get("entry_type") == "nodeGossipReceipt"
    ]
    trusted = [entry for entry in gossip if entry.get("signature_valid") is True]
    consensus = policy_hash_consensus([
        {
            **(entry.get("summary") or {}),
            "signature_valid": entry.get("signature_valid"),
            "trust_level": entry.get("trust_level"),
        }
        for entry in gossip
    ])
    return {
        "peers": load_peers(),
        "gossip_events": len(gossip),
        "trusted_gossip_events": len(trusted),
        "consensus": consensus,
        "mesh": get_mesh(),
        "alerts": len(list_alerts()),
    }


def _flatten_continuity_event(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data") or {}
    decision = data.get("decision") or {}
    return {
        "event_id": event.get("event_id") or event.get("receipt_hash"),
        "timestamp": event.get("timestamp"),
        "kind": event.get("kind") or event.get("entry_type"),
        "trace_id": event.get("trace_id") or data.get("trace_id") or decision.get("trace_id"),
        "decision": decision.get("decision") or event.get("decision"),
        "payload": data.get("payload"),
    }
