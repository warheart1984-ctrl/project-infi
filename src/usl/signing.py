"""ed25519 signing for USL Voss transitions."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.usl.types import CryptoInfo, SignatureInfo, VossTransition

ALGO_ED25519 = "ed25519"
ENV_USL_SIGNING_KEY = "USL_SIGNING_KEY"
ENV_USL_SIGNING_KEY_ID = "USL_SIGNING_KEY_ID"


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[2] / ".runtime"


def _signing_key_path(runtime_dir: Path) -> Path:
    return runtime_dir / "usl" / "signing-key.json"


def _load_or_create_keypair(
    runtime_dir: Path | None = None,
    *,
    create_if_missing: bool = True,
) -> tuple[Any, str]:
    """Return (SigningKey, key_id). Uses cryptography if available."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import (
            Encoding,
            NoEncryption,
            PrivateFormat,
            PublicFormat,
        )
    except ImportError as exc:
        raise RuntimeError(
            "cryptography package required for USL ed25519 signing"
        ) from exc

    env_key = os.getenv(ENV_USL_SIGNING_KEY, "").strip()
    env_key_id = os.getenv(ENV_USL_SIGNING_KEY_ID, "").strip() or "env:usl-signing"

    if env_key:
        raw = base64.b64decode(env_key)
        key = Ed25519PrivateKey.from_private_bytes(raw)
        return key, env_key_id

    root = runtime_dir or _default_runtime_dir()
    path = _signing_key_path(root)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = base64.b64decode(str(payload["private_key_b64"]))
        key_id = str(payload.get("key_id") or "usl-default")
        return Ed25519PrivateKey.from_private_bytes(raw), key_id

    if not create_if_missing:
        raise FileNotFoundError(f"USL signing key not found at {path}")

    key = Ed25519PrivateKey.generate()
    key_id = str(uuid4())
    path.parent.mkdir(parents=True, exist_ok=True)
    private_bytes = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_bytes = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    path.write_text(
        json.dumps(
            {
                "key_id": key_id,
                "private_key_b64": base64.b64encode(private_bytes).decode("ascii"),
                "public_key_b64": base64.b64encode(public_bytes).decode("ascii"),
                "algo": ALGO_ED25519,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return key, key_id


def sign_transition(
    transition: VossTransition,
    *,
    runtime_dir: Path | None = None,
    signer_id: str | None = None,
) -> SignatureInfo:
    """Sign event_hash with ed25519."""
    key, key_id = _load_or_create_keypair(runtime_dir)
    message = transition.crypto.event_hash.encode("utf-8")
    sig_bytes = key.sign(message)
    return SignatureInfo(
        signer_id=signer_id or key_id,
        algo=ALGO_ED25519,
        sig=base64.b64encode(sig_bytes).decode("ascii"),
    )


def verify_transition_signature(
    transition: VossTransition,
    public_key_b64: str | None = None,
    *,
    runtime_dir: Path | None = None,
) -> bool:
    """Verify ed25519 signature on transition."""
    if not transition.crypto.signature:
        return False
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.exceptions import InvalidSignature
    except ImportError:
        return False

    if public_key_b64 is None:
        root = runtime_dir or _default_runtime_dir()
        path = _signing_key_path(root)
        if not path.exists():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        public_key_b64 = str(payload["public_key_b64"])

    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
    sig = base64.b64decode(transition.crypto.signature.sig)
    try:
        pub.verify(sig, transition.crypto.event_hash.encode("utf-8"))
        return True
    except InvalidSignature:
        return False


def attach_signature(
    transition: VossTransition,
    *,
    runtime_dir: Path | None = None,
) -> VossTransition:
    """Sign and attach signature to transition crypto block."""
    transition.crypto.signature = sign_transition(transition, runtime_dir=runtime_dir)
    return transition
