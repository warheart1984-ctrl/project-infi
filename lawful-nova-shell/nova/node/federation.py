from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from nova.node.identity import NodeIdentity, sign_payload, verify_payload_signature
from nova.node.ledger import append_ledger, runtime_dir
from nova.node.policy import load_node_policy

router = APIRouter()


def peers_path() -> Path:
    return Path(os.environ.get("NOVA_NODE_PEERS_PATH", str(runtime_dir() / "peers.json")))


def load_peers() -> list[dict[str, Any]]:
    path = peers_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def gossip_summary() -> dict[str, Any]:
    ident = NodeIdentity.load("./policy.yaml")
    return {
        "node_id": ident.node_id,
        "operator_id": ident.operator_id,
        "timestamp": int(time.time()),
        "policy_hash": ident.policy_hash,
        "capabilities": ["chat", "governance", "audit"],
    }


def signed_gossip_summary() -> dict[str, Any]:
    summary = gossip_summary()
    return {
        "summary": summary,
        "signature": sign_payload(summary),
        "signature_algorithm": "rsa-sha256-digest",
    }


def gossip_to_peers() -> list[dict[str, Any]]:
    summary = signed_gossip_summary()
    results: list[dict[str, Any]] = []
    for peer in load_peers():
        peer_id = str(peer.get("peer_id") or "unknown-peer")
        endpoint = str(peer.get("endpoint") or "").rstrip("/")
        if not endpoint:
            results.append({"peer_id": peer_id, "status": "error", "error": "missing endpoint"})
            continue
        request = urllib.request.Request(
            f"{endpoint}/node/gossip",
            data=json.dumps(summary).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                results.append({"peer_id": peer_id, "status": response.status})
        except (urllib.error.URLError, TimeoutError) as exc:
            results.append({"peer_id": peer_id, "status": "error", "error": str(exc)})
    return results


@router.post("/node/gossip")
async def receive_gossip(request: Request) -> dict[str, Any]:
    data = await request.json()
    return receive_gossip_payload(data)


def receive_gossip_payload(data: dict[str, Any]) -> dict[str, Any]:
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else data
    signature = data.get("signature")
    signature_valid = verify_payload_signature(summary, signature)
    trust_level = "trusted" if signature_valid else "invalid"
    entry = append_ledger({
        "entry_type": "nodeGossipReceipt",
        "timestamp": int(time.time()),
        "summary": summary,
        "signature_valid": signature_valid,
        "trust_level": trust_level,
    })
    return {
        "ack": True,
        "received_at": entry["timestamp"],
        "signature_valid": signature_valid,
        "trust_level": trust_level,
    }


def node_hello() -> dict[str, Any]:
    policy = load_node_policy()
    payload = {
        "node_id": policy["node_id"],
        "operator_id": policy["operator_id"],
        "policy_version": policy["policy_version"],
        "policy_hash": policy["policy_hash"],
        "capabilities": ["chat", "governance", "audit"],
    }
    return {
        **payload,
        "signature": sign_payload(payload),
        "signature_algorithm": "rsa-sha256-digest",
        "trust_level": "self",
    }


@router.post("/node/hello")
async def hello() -> dict[str, Any]:
    return node_hello()
