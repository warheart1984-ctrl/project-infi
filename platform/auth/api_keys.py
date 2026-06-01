"""API key hashing and verification."""

from __future__ import annotations

import hashlib
import hmac


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def verify_api_key(*, provided: str, expected_hash: str) -> bool:
    if not provided or not expected_hash:
        return False
    digest = hash_api_key(provided)
    return hmac.compare_digest(digest, expected_hash)
