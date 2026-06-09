"""Evaluate path hooks for mesh peer trust and falsity recording."""

from __future__ import annotations

from flask import Request

from src.mesh.capabilities_enforcement import check_evaluate_capability
from src.mesh.falsity_adapter import get_falsity_mesh_adapter
from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import mesh_base
from src.mesh.topology import load_mesh_config
from src.mesh.trust import TrustStore


def get_mesh_peer_id(request: Request) -> str | None:
    peer = request.headers.get("X-Mesh-Peer-Id")
    if not peer:
        return None
    peer = str(peer).strip()
    return peer or None


def check_mesh_peer_allowed(peer_id: str | None, base_dir: str | None = None) -> tuple[bool, str | None]:
    if not peer_id:
        return True, None
    root = base_dir or mesh_base()
    config = load_mesh_config(root)
    if config.get("require_handshake") and not KnownPeersStore(root).is_known(peer_id):
        return False, "mesh_peer_not_handshaken"
    cap_ok, cap_reason = check_evaluate_capability(peer_id, root)
    if not cap_ok:
        return False, cap_reason
    return True, None


def apply_mesh_trust_penalty(normalized_packet: dict, peer_id: str | None, base_dir: str | None = None) -> dict:
    if not peer_id:
        return normalized_packet
    penalty = TrustStore(base_dir).penalty_for_peer(peer_id)
    if penalty <= 0:
        return normalized_packet
    packet = dict(normalized_packet)
    payload = dict(packet.get("payload") or {})
    confidence = float(payload.get("confidence") or 0.0)
    payload["confidence"] = max(0.0, confidence - penalty)
    packet["payload"] = payload
    return packet


def record_mesh_evaluate_outcome(
    peer_id: str | None,
    payload: dict,
    normalized_packet: dict,
    *,
    base_dir: str | None = None,
) -> None:
    if not peer_id:
        return
    root = base_dir or mesh_base()
    trust = TrustStore(root)
    status = payload.get("status")
    if status == "ADMIT":
        trust.record(peer_id, "evaluate_admit")
    elif status == "REJECT":
        trust.record(peer_id, "evaluate_reject")

    if status != "REJECT":
        return
    if payload.get("reason") != "rls_rejected":
        return

    claim = (normalized_packet.get("payload") or {}).get("claim") or ""
    if not claim:
        return
    get_falsity_mesh_adapter(root).append_from_reject(
        claim,
        reason="rls_rejected",
        source_node=peer_id,
    )


def mesh_base_dir() -> str:
    return mesh_base()
