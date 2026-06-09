"""Stable node identity for mesh participation."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.mesh.paths import mesh_dir

IDENTITY_FILENAME = "node_identity.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def identity_path(base_dir: str | Path | None = None) -> Path:
    return mesh_dir(base_dir) / IDENTITY_FILENAME


def _derive_verify_key(node_secret: str) -> str:
    seed = hashlib.sha256(node_secret.encode("utf-8")).digest()
    return hashlib.sha256(b"mesh-verify:" + seed).hexdigest()


def hmac_sha256_hex(key: str, message: str) -> str:
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def hmac_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


def load_or_create_identity(base_dir: str | Path | None = None) -> dict:
    path = identity_path(base_dir)
    if path.exists():
        identity = json.loads(path.read_text(encoding="utf-8"))
        return _ensure_verify_key(identity, path)

    node_secret = secrets.token_hex(32)
    identity = {
        "node_id": str(uuid.uuid4()),
        "node_secret": node_secret,
        "verify_key": _derive_verify_key(node_secret),
        "created_at": _utc_now(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    return identity


def _ensure_verify_key(identity: dict, path: Path) -> dict:
    if identity.get("verify_key"):
        return identity
    identity["verify_key"] = _derive_verify_key(identity["node_secret"])
    path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    return identity


def node_fingerprint(identity: dict) -> str:
    raw = f"{identity['node_id']}:{identity.get('created_at', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def public_node_record(identity: dict, *, capabilities: list[str] | None = None) -> dict:
    verify_key = identity.get("verify_key") or _derive_verify_key(identity["node_secret"])
    return {
        "node_id": identity["node_id"],
        "fingerprint": node_fingerprint(identity),
        "verify_key": verify_key,
        "capabilities": capabilities or [],
    }


def verify_ack_signature(verify_key: str, nonce: str, signature: str) -> bool:
    if not verify_key or not nonce or not signature or len(signature) != 64:
        return False
    expected = hmac_sha256_hex(verify_key, nonce)
    return hmac_compare(expected, signature)
