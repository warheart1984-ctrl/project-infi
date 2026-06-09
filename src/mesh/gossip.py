"""Gossip protocol for falsity ledger and invariant sync on AAIS."""

from __future__ import annotations

import logging

import requests

from src.mesh.falsity_adapter import get_falsity_mesh_adapter
from src.mesh.gossip_runtime import is_peer_in_backoff
from src.mesh.handshake import build_ack, build_hello, complete_handshake, handle_hello
from src.mesh.invariants import InvariantStore
from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import mesh_base
from src.mesh.topology import iter_all_peers, pinned_verify_key_for_url, verify_key_allowed
from src.mesh.trust import TrustStore

logger = logging.getLogger(__name__)

MESH_PEER_HEADER = "X-Mesh-Peer-Id"


def _mesh_headers(identity: dict) -> dict[str, str]:
    return {MESH_PEER_HEADER: identity["node_id"]}


def _sync_gossip_payload(
    base_dir: str,
    peer_url: str,
    ledger,
    invariants: InvariantStore,
    *,
    headers: dict[str, str] | None = None,
) -> None:
    hdrs = headers or {}
    try:
        g = requests.post(
            f"{peer_url}/api/mesh/gossip",
            json={"falsity_head": ledger.head_hash(), "invariant_digest": invariants.digest()},
            headers=hdrs,
            timeout=10,
        )
        g.raise_for_status()
        payload = g.json()
        ledger.merge_entries(payload.get("falsity_entries", []))
        if payload.get("invariants"):
            invariants.merge(payload["invariants"])
    except requests.RequestException as exc:
        logger.warning("gossip pull failed for %s: %s", peer_url, exc)
        raise


def _maybe_gossip_push(
    base_dir: str,
    config: dict,
    peer_url: str,
    ledger,
    invariants: InvariantStore,
    *,
    headers: dict[str, str] | None = None,
) -> None:
    if not config.get("gossip_push"):
        return
    hdrs = headers or {}
    try:
        requests.post(
            f"{peer_url}/api/mesh/gossip",
            json={
                "falsity_head": ledger.head_hash(),
                "invariant_digest": invariants.digest(),
                "push_entries": ledger.export_since_head(None)[-50:],
                "invariants": invariants.load(),
            },
            headers=hdrs,
            timeout=10,
        ).raise_for_status()
    except requests.RequestException as exc:
        logger.warning("gossip push failed for %s: %s", peer_url, exc)


def gossip_pull(base_dir: str, identity: dict, config: dict, peer_url: str) -> dict:
    peer_url = peer_url.rstrip("/")
    if is_peer_in_backoff(peer_url):
        return {"peer": peer_url, "ok": False, "error": "peer_in_backoff", "skipped": True}

    ledger = get_falsity_mesh_adapter(base_dir)
    invariants = InvariantStore(base_dir)
    trust = TrustStore(base_dir)
    known = KnownPeersStore(base_dir)
    headers = _mesh_headers(identity)

    pinned = pinned_verify_key_for_url(config, peer_url)
    hello = build_hello(
        identity,
        config,
        falsity_head=ledger.head_hash(),
        invariant_digest=invariants.digest(),
    )
    if pinned:
        hello["node"]["verify_key"] = pinned

    try:
        r = requests.post(
            f"{peer_url}/api/mesh/handshake",
            json=hello,
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        challenge = r.json()
    except requests.RequestException as exc:
        logger.warning("handshake HELLO failed for %s: %s", peer_url, exc)
        return {"peer": peer_url, "ok": False, "error": str(exc)}

    if challenge.get("phase") != "CHALLENGE":
        remote_node = hello.get("node") or {}
        peer_id = remote_node.get("node_id")
        if peer_id:
            trust.record(peer_id, "handshake_fail")
        return {"peer": peer_url, "ok": False, "error": "unexpected_handshake_phase"}

    nonce = challenge.get("nonce")
    ack = build_ack(identity, nonce)
    try:
        r2 = requests.post(
            f"{peer_url}/api/mesh/handshake/ack",
            json=ack,
            headers=headers,
            timeout=10,
        )
        r2.raise_for_status()
        result = r2.json()
    except requests.RequestException as exc:
        remote_node = challenge.get("node") or {}
        peer_id = remote_node.get("node_id")
        if peer_id:
            trust.record(peer_id, "gossip_fail")
        logger.warning("handshake ACK failed for %s: %s", peer_url, exc)
        return {"peer": peer_url, "ok": False, "error": str(exc)}

    remote_node = challenge.get("node") or {}
    peer_id = remote_node.get("node_id") or peer_url

    if result.get("ok"):
        known.register(
            peer_id,
            fingerprint=remote_node.get("fingerprint"),
            verify_key=remote_node.get("verify_key"),
            capabilities=(challenge.get("negotiation") or {}).get("intersection", []),
            peer_url=peer_url,
        )

    if challenge.get("falsity_head") == ledger.head_hash():
        trust.record(peer_id, "ledger_agree")
    else:
        trust.record(peer_id, "ledger_diverge")
        try:
            _sync_gossip_payload(base_dir, peer_url, ledger, invariants, headers=headers)
        except requests.RequestException:
            trust.record(peer_id, "gossip_fail")

    if challenge.get("invariant_digest") != invariants.digest():
        try:
            _sync_gossip_payload(base_dir, peer_url, ledger, invariants, headers=headers)
        except requests.RequestException:
            trust.record(peer_id, "gossip_fail")

    _maybe_gossip_push(base_dir, config, peer_url, ledger, invariants, headers=headers)

    trust.record(peer_id, "handshake_ok" if result.get("ok") else "handshake_fail")
    if result.get("ok"):
        trust.record(peer_id, "gossip_ok")

    return {
        "peer": peer_url,
        "peer_node_id": peer_id,
        "ok": bool(result.get("ok")),
        "negotiation": challenge.get("negotiation"),
        "falsity_head": ledger.head_hash(),
        "invariant_digest": invariants.digest(),
    }


def gossip_all(base_dir: str, identity: dict, config: dict) -> list[dict]:
    results = []
    for peer in iter_all_peers(config, base_dir):
        url = peer.get("url")
        if url:
            results.append(gossip_pull(base_dir, identity, config, url))
    return results


def handle_inbound_hello(base_dir: str, identity: dict, config: dict, hello: dict) -> dict:
    ledger = get_falsity_mesh_adapter(base_dir)
    invariants = InvariantStore(base_dir)
    remote_vk = (hello.get("node") or {}).get("verify_key")
    if not verify_key_allowed(config, remote_vk):
        return {"phase": "ERROR", "reason": "verify_key_not_pinned"}
    return handle_hello(
        identity,
        config,
        hello,
        falsity_head=ledger.head_hash(),
        invariant_digest=invariants.digest(),
        base_dir=base_dir,
    )


def handle_inbound_ack(base_dir: str, identity: dict, config: dict, ack: dict, *, peer_url: str | None = None) -> dict:
    from src.mesh.handshake import _get_pending_item

    remote_id = ack.get("node_id")
    pending = _get_pending_item(base_dir, remote_id)
    if pending:
        hello = pending.get("hello") or {}
        remote_vk = (hello.get("node") or {}).get("verify_key")
        if not verify_key_allowed(config, remote_vk):
            from src.mesh.handshake import _pop_pending_item

            _pop_pending_item(base_dir, remote_id)
            return {"ok": False, "reason": "verify_key_not_pinned", "peer_node_id": remote_id}

    pinned = pinned_verify_key_for_url(config, peer_url) if peer_url else None
    result = complete_handshake(identity, ack, pinned_verify_key=pinned, base_dir=base_dir)
    if result.get("ok"):
        known = KnownPeersStore(base_dir)
        known.register(
            result["peer_node_id"],
            fingerprint=result.get("peer_fingerprint"),
            verify_key=result.get("peer_verify_key"),
            capabilities=(result.get("negotiation") or {}).get("intersection", []),
            peer_url=peer_url,
        )
    return result


def build_gossip_response(base_dir: str, request_body: dict) -> dict:
    ledger = get_falsity_mesh_adapter(base_dir)
    invariants = InvariantStore(base_dir)
    known_head = request_body.get("falsity_head")

    push_entries = request_body.get("push_entries") or []
    if push_entries:
        ledger.merge_entries(push_entries)
    if request_body.get("invariants"):
        invariants.merge(request_body["invariants"])

    return {
        "falsity_head": ledger.head_hash(),
        "falsity_entries": ledger.export_since_head(known_head),
        "invariants": invariants.load(),
        "invariant_digest": invariants.digest(),
    }


def default_mesh_base() -> str:
    return mesh_base()
