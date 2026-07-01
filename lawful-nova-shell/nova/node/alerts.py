from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter

from nova.node.ledger import read_jsonl, read_ledger, runtime_dir
from nova.node.mesh import get_mesh

router = APIRouter()


def list_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    now = int(time.time())
    for entry in read_ledger():
        if entry.get("entry_type") == "nodeGossipReceipt" and entry.get("signature_valid") is False:
            summary = entry.get("summary") or {}
            node_id = str(summary.get("node_id") or "unknown-peer")
            alerts.append(
                {
                    "id": f"invalid-signature-{node_id}",
                    "timestamp": entry.get("timestamp", now),
                    "severity": "error",
                    "category": "federation",
                    "message": "Invalid gossip signature",
                    "context": {"node_id": node_id},
                }
            )
    mesh = get_mesh()
    for node_id in mesh.get("divergent_peers", []):
        alerts.append(
            {
                "id": f"policy-drift-{node_id}",
                "timestamp": now,
                "severity": "warn",
                "category": "policy",
                "message": "Peer policy hash diverges from local node",
                "context": {"node_id": node_id},
            }
        )
    blocked_by_caller: dict[str, int] = {}
    for event in read_jsonl(runtime_dir() / "rate-limits.jsonl"):
        if event.get("blocked"):
            caller = str(event.get("caller_id") or "unknown")
            blocked_by_caller[caller] = blocked_by_caller.get(caller, 0) + 1
    for caller, count in blocked_by_caller.items():
        alerts.append(
            {
                "id": f"rate-limit-{caller}",
                "timestamp": now,
                "severity": "info",
                "category": "rate-limit",
                "message": "Rate-limit block recorded",
                "context": {"caller_id": caller, "blocked_count": count},
            }
        )
    return alerts


@router.get("/node/alerts")
async def alerts() -> dict[str, list[dict[str, Any]]]:
    return {"alerts": list_alerts()}
