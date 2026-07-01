from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from nova.node.consensus import policy_hash_consensus
from nova.node.federation import load_peers
from nova.node.ledger import read_ledger
from nova.node.policy import load_node_policy

router = APIRouter()


def get_mesh() -> dict[str, Any]:
    local = load_node_policy()
    peers = _ledger_peers()
    configured = [
        {
            "node_id": str(peer.get("peer_id") or peer.get("node_id") or "unknown-peer"),
            "trust_level": str(peer.get("trust_level") or "limited"),
            "policy_hash": peer.get("policy_hash"),
            "last_hello": peer.get("last_hello"),
            "last_gossip": peer.get("last_gossip"),
            "signature_valid": peer.get("signature_valid"),
            "configured": True,
        }
        for peer in load_peers()
    ]
    known_ids = {peer["node_id"] for peer in peers}
    peers.extend(peer for peer in configured if peer["node_id"] not in known_ids)
    summaries = [
        {
            "policy_hash": peer.get("policy_hash"),
            "signature_valid": peer.get("signature_valid"),
            "trust_level": peer.get("trust_level"),
        }
        for peer in peers
    ]
    summaries.append({"policy_hash": local["policy_hash"], "trust_level": "self", "signature_valid": True})
    consensus = policy_hash_consensus(summaries)
    divergent = [
        peer["node_id"]
        for peer in peers
        if peer.get("policy_hash") and peer.get("policy_hash") != local["policy_hash"]
    ]
    return {
        "node_id": local["node_id"],
        "local_policy_hash": local["policy_hash"],
        "peers": peers,
        "consensus_ratio": consensus["agreement_ratio"],
        "consensus": consensus,
        "divergent_peers": divergent,
    }


@router.get("/node/mesh")
async def mesh() -> dict[str, Any]:
    return get_mesh()


def _ledger_peers() -> list[dict[str, Any]]:
    peers: dict[str, dict[str, Any]] = {}
    for entry in read_ledger():
        if entry.get("entry_type") not in {"nodeGossipReceipt", "nodeHandshakeReceipt"}:
            continue
        summary = entry.get("summary") or entry.get("hello") or {}
        node_id = str(summary.get("node_id") or "unknown-peer")
        peers[node_id] = {
            "node_id": node_id,
            "trust_level": str(entry.get("trust_level") or "limited"),
            "policy_hash": summary.get("policy_hash"),
            "last_hello": entry.get("timestamp") if entry.get("entry_type") == "nodeHandshakeReceipt" else None,
            "last_gossip": entry.get("timestamp") if entry.get("entry_type") == "nodeGossipReceipt" else None,
            "signature_valid": entry.get("signature_valid"),
        }
    return list(peers.values())
