"""Multi-node handshake: HELLO → CHALLENGE → ACK."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.mesh.capabilities import capability_advertisement, negotiate
from src.mesh.identity import (
    hmac_sha256_hex,
    node_fingerprint,
    public_node_record,
    verify_ack_signature,
)
from src.mesh.paths import mesh_dir

PENDING_FILENAME = "handshake_pending.json"
PENDING_TTL = timedelta(minutes=5)

_pending: dict[str, dict] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _pending_path(base_dir: str | Path | None) -> Path | None:
    if base_dir is None:
        return None
    return mesh_dir(base_dir) / PENDING_FILENAME


def _serialize_pending(data: dict) -> dict:
    out = dict(data)
    expires = out.get("expires_at")
    if isinstance(expires, datetime):
        out["expires_at"] = expires.isoformat()
    return out


def _deserialize_pending(data: dict) -> dict:
    out = dict(data)
    expires = out.get("expires_at")
    if isinstance(expires, str):
        out["expires_at"] = datetime.fromisoformat(expires)
    return out


def _load_file_pending(base_dir: str | Path) -> dict[str, dict]:
    path = _pending_path(base_dir)
    if path is None or not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {k: _deserialize_pending(v) for k, v in raw.items()}


def _save_file_pending(base_dir: str | Path, data: dict[str, dict]) -> None:
    path = _pending_path(base_dir)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = {k: _serialize_pending(v) for k, v in data.items()}
    path.write_text(json.dumps(serialized, indent=2), encoding="utf-8")


def _get_pending_store(base_dir: str | Path | None) -> dict[str, dict]:
    if base_dir is not None:
        return _load_file_pending(base_dir)
    return _pending


def _set_pending_item(base_dir: str | Path | None, remote_id: str, data: dict) -> None:
    if base_dir is not None:
        store = _load_file_pending(base_dir)
        store[remote_id] = data
        _save_file_pending(base_dir, store)
    else:
        _pending[remote_id] = data


def _pop_pending_item(base_dir: str | Path | None, remote_id: str) -> dict | None:
    if base_dir is not None:
        store = _load_file_pending(base_dir)
        item = store.pop(remote_id, None)
        _save_file_pending(base_dir, store)
        return item
    return _pending.pop(remote_id, None)


def _get_pending_item(base_dir: str | Path | None, remote_id: str) -> dict | None:
    store = _get_pending_store(base_dir)
    return store.get(remote_id)


def build_hello(identity: dict, config: dict, *, falsity_head: str, invariant_digest: str) -> dict:
    caps = capability_advertisement(config)
    return {
        "phase": "HELLO",
        "node": public_node_record(identity, capabilities=caps),
        "node_name": config.get("node_name"),
        "falsity_head": falsity_head,
        "invariant_digest": invariant_digest,
        "timestamp": _utc_now().isoformat(),
    }


def handle_hello(
    identity: dict,
    config: dict,
    hello: dict,
    *,
    falsity_head: str,
    invariant_digest: str,
    base_dir: str | Path | None = None,
) -> dict:
    remote = hello.get("node") or {}
    remote_id = remote.get("node_id")
    if not remote_id:
        return {"phase": "ERROR", "reason": "missing_node_id"}
    if not remote.get("verify_key"):
        return {"phase": "ERROR", "reason": "missing_verify_key"}

    nonce = secrets.token_hex(16)
    local_caps = capability_advertisement(config)
    remote_caps = remote.get("capabilities") or []
    negotiation = negotiate(local_caps, remote_caps)

    _set_pending_item(
        base_dir,
        remote_id,
        {
            "nonce": nonce,
            "expires_at": _utc_now() + PENDING_TTL,
            "hello": hello,
            "negotiation": negotiation,
        },
    )

    return {
        "phase": "CHALLENGE",
        "nonce": nonce,
        "node": public_node_record(identity, capabilities=local_caps),
        "negotiation": negotiation,
        "falsity_head": falsity_head,
        "invariant_digest": invariant_digest,
    }


def build_ack(identity: dict, nonce: str) -> dict:
    verify_key = identity.get("verify_key") or public_node_record(identity)["verify_key"]
    sig = hmac_sha256_hex(verify_key, nonce)
    return {
        "phase": "ACK",
        "node_id": identity["node_id"],
        "fingerprint": node_fingerprint(identity),
        "verify_key": verify_key,
        "nonce": nonce,
        "signature": sig,
    }


def complete_handshake(
    identity: dict,
    ack: dict,
    *,
    pinned_verify_key: str | None = None,
    base_dir: str | Path | None = None,
) -> dict:
    remote_id = ack.get("node_id")
    pending = _pop_pending_item(base_dir, remote_id)
    if not pending:
        return {"ok": False, "reason": "unknown_or_expired_challenge"}

    if _utc_now() > pending["expires_at"]:
        return {"ok": False, "reason": "challenge_expired"}

    nonce = pending["nonce"]
    sig = ack.get("signature", "")
    if ack.get("nonce") != nonce:
        return {"ok": False, "reason": "nonce_mismatch"}

    hello = pending.get("hello") or {}
    remote = hello.get("node") or {}
    verify_key = remote.get("verify_key") or ack.get("verify_key") or pinned_verify_key
    if not verify_key:
        return {"ok": False, "reason": "missing_verify_key"}

    if pinned_verify_key and pinned_verify_key != verify_key:
        return {"ok": False, "reason": "verify_key_pin_mismatch"}

    if not verify_ack_signature(verify_key, nonce, sig):
        return {"ok": False, "reason": "invalid_signature"}

    return {
        "ok": True,
        "peer_node_id": remote_id,
        "peer_fingerprint": ack.get("fingerprint"),
        "peer_verify_key": verify_key,
        "peer_capabilities": remote.get("capabilities", []),
        "peer_falsity_head": hello.get("falsity_head"),
        "peer_invariant_digest": hello.get("invariant_digest"),
        "negotiation": pending.get("negotiation"),
    }


def verify_ack_from_known_peer(peer_verify_key: str | None, ack: dict) -> bool:
    if not peer_verify_key:
        return False
    nonce = ack.get("nonce", "")
    sig = ack.get("signature", "")
    return verify_ack_signature(peer_verify_key, nonce, sig)
