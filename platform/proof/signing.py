"""Attestation signatures: HMAC (v25) and Ed25519 (v35)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from typing import Any

SIGNATURE_ALGS = frozenset({"hmac-sha256", "ed25519"})


def default_signature_alg() -> str:
    alg = os.environ.get("PLATFORM_ATTESTATION_ALG", "hmac-sha256").strip().lower()
    return alg if alg in SIGNATURE_ALGS else "hmac-sha256"


def attestation_secret() -> str:
    return os.environ.get("PLATFORM_ATTESTATION_SECRET", "platform-attest-dev-secret")


def attestation_message(*, job_id: str, runner_id: str, result_hash: str) -> bytes:
    return f"{job_id}:{runner_id}:{result_hash}".encode()


def sign_hmac(*, job_id: str, runner_id: str, result_hash: str) -> str:
    body = attestation_message(job_id=job_id, runner_id=runner_id, result_hash=result_hash)
    return hmac.new(attestation_secret().encode(), body, hashlib.sha256).hexdigest()


def verify_hmac(
    *,
    job_id: str,
    runner_id: str,
    result_hash: str,
    signature: str,
) -> bool:
    if not signature:
        return os.environ.get("PLATFORM_ATTESTATION_SECRET") is None
    expected = sign_hmac(job_id=job_id, runner_id=runner_id, result_hash=result_hash)
    return hmac.compare_digest(expected, signature)


def _load_ed25519_public_key(pem_or_b64: str) -> Any:
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
    except ImportError as exc:
        raise RuntimeError("cryptography package required for ed25519") from exc
    text = pem_or_b64.strip()
    if text.startswith("-----"):
        return load_pem_public_key(text.encode())
    raw = base64.b64decode(text)
    from cryptography.hazmat.primitives.serialization import load_der_public_key

    return load_der_public_key(raw)


def _load_ed25519_private_key(pem: str) -> Any:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    return load_pem_private_key(pem.encode(), password=None)


def sign_ed25519(
    *,
    job_id: str,
    runner_id: str,
    result_hash: str,
    private_key_pem: str,
) -> str:
    key = _load_ed25519_private_key(private_key_pem)
    sig = key.sign(attestation_message(job_id=job_id, runner_id=runner_id, result_hash=result_hash))
    return base64.b64encode(sig).decode()


def verify_ed25519(
    *,
    job_id: str,
    runner_id: str,
    result_hash: str,
    signature: str,
    public_key_pem: str,
) -> bool:
    if not signature or not public_key_pem:
        return False
    try:
        key = _load_ed25519_public_key(public_key_pem)
        key.verify(
            base64.b64decode(signature),
            attestation_message(job_id=job_id, runner_id=runner_id, result_hash=result_hash),
        )
        return True
    except Exception:
        return False


def sign_attestation(
    *,
    job_id: str,
    runner_id: str,
    result_hash: str,
    signature_alg: str = "",
    private_key_pem: str = "",
) -> tuple[str, str]:
    alg = signature_alg or default_signature_alg()
    if alg == "ed25519":
        pem = private_key_pem or os.environ.get("PLATFORM_RUNNER_PRIVATE_KEY_PEM", "")
        if not pem:
            raise ValueError("ed25519 requires private_key_pem or PLATFORM_RUNNER_PRIVATE_KEY_PEM")
        return sign_ed25519(
            job_id=job_id,
            runner_id=runner_id,
            result_hash=result_hash,
            private_key_pem=pem,
        ), alg
    return sign_hmac(job_id=job_id, runner_id=runner_id, result_hash=result_hash), "hmac-sha256"


def verify_attestation_signature(
    *,
    job_id: str,
    runner_id: str,
    result_hash: str,
    signature: str,
    signature_alg: str = "",
    public_key_pem: str = "",
) -> bool:
    alg = signature_alg or default_signature_alg()
    if alg == "ed25519":
        return verify_ed25519(
            job_id=job_id,
            runner_id=runner_id,
            result_hash=result_hash,
            signature=signature,
            public_key_pem=public_key_pem,
        )
    return verify_hmac(job_id=job_id, runner_id=runner_id, result_hash=result_hash, signature=signature)
