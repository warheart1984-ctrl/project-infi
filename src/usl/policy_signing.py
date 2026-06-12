"""Sign and verify USL lawbook policy under sigil:lambda-root."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.usl.signing import ALGO_ED25519, _load_or_create_keypair, verify_transition_signature
from src.usl.types import CryptoInfo, SignatureInfo, VossTransition
from src.usl.voss_ledger import GENESIS_ROOT

SIGIL_LAMBDA_ROOT = "sigil:lambda-root"
POLICY_SCHEMA = "usl-lawbook-signed.v1"


def _minimal_transition_for_policy(event_hash: str, signature: SignatureInfo) -> VossTransition:
    from src.usl.types import (
        ActorInfo,
        CapabilityInfo,
        ContextInfo,
        LawInfo,
        ResourceInfo,
        StateInfo,
        VossInfo,
    )

    return VossTransition(
        version="v1",
        transition_id="policy-sign",
        timestamp="1970-01-01T00:00:00+00:00",
        actor=ActorInfo("policy", "daily-driver", "system", SIGIL_LAMBDA_ROOT),
        context=ContextInfo("policy", "0", "0", "policy", "usl-node-1"),
        capability=CapabilityInfo("policy.sign", "policy", ResourceInfo("policy", "lawbook")),
        state=StateInfo(GENESIS_ROOT, GENESIS_ROOT, GENESIS_ROOT, __import__("src.usl.types", fromlist=["DeltaSummary"]).DeltaSummary()),
        law=LawInfo("policy:sign", "lawbook:usl-v1", "allow", "policy_sign"),
        voss=VossInfo("λ:policy", "debt:0", "scar:0", 0, "lane:policy"),
        crypto=CryptoInfo(event_hash=event_hash, prev_ledger_root=GENESIS_ROOT, ledger_root=GENESIS_ROOT, signature=signature),
    )


def sign_lawbook(
    lawbook: dict[str, Any],
    *,
    runtime_dir: Path | None = None,
    sigil_id: str = SIGIL_LAMBDA_ROOT,
) -> dict[str, Any]:
    """Sign lawbook payload; returns envelope with signature block."""
    import base64
    import hashlib

    from src.usl.signing import sign_transition

    canonical = json.dumps(lawbook, sort_keys=True, separators=(",", ":")).encode("utf-8")
    event_hash = f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    key, key_id = _load_or_create_keypair(runtime_dir)
    message = event_hash.encode("utf-8")
    sig_bytes = key.sign(message)
    signature = SignatureInfo(
        signer_id=key_id,
        algo=ALGO_ED25519,
        sig=base64.b64encode(sig_bytes).decode("ascii"),
    )

    transition = _minimal_transition_for_policy(event_hash, signature)
    if not verify_transition_signature(transition, runtime_dir=runtime_dir):
        raise RuntimeError("policy self-verify failed after sign")

    return {
        "schema": POLICY_SCHEMA,
        "sigil_id": sigil_id,
        "lawbook": lawbook,
        "crypto": {
            "event_hash": event_hash,
            "signature": {
                "signer_id": signature.signer_id,
                "algo": signature.algo,
                "sig": signature.sig,
            },
        },
    }


def verify_signed_policy(
    path: Path,
    *,
    expected_sigil: str = SIGIL_LAMBDA_ROOT,
    runtime_dir: Path | None = None,
) -> tuple[bool, str]:
    """Verify signed policy file at guest load."""
    if not path.is_file():
        return False, "file_not_found"

    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, "invalid_json"

    if envelope.get("schema") != POLICY_SCHEMA:
        return False, "wrong_schema"
    if envelope.get("sigil_id") != expected_sigil:
        return False, "sigil_mismatch"

    crypto = envelope.get("crypto") or {}
    sig_block = crypto.get("signature") or {}
    event_hash = str(crypto.get("event_hash") or "")
    if not event_hash or not sig_block.get("sig"):
        return False, "missing_signature"

    signature = SignatureInfo(
        signer_id=str(sig_block.get("signer_id", "")),
        algo=str(sig_block.get("algo", ALGO_ED25519)),
        sig=str(sig_block["sig"]),
    )
    transition = _minimal_transition_for_policy(event_hash, signature)
    if not verify_transition_signature(transition, runtime_dir=runtime_dir):
        return False, "signature_invalid"

    lawbook = envelope.get("lawbook")
    if not isinstance(lawbook, dict):
        return False, "lawbook_missing"

    canonical = json.dumps(lawbook, sort_keys=True, separators=(",", ":")).encode("utf-8")
    import hashlib

    expected = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
    if expected != event_hash:
        return False, "lawbook_tampered"

    return True, "verified"
