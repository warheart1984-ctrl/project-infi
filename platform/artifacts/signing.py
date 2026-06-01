"""Signed artifact download URLs."""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import quote


def sign_download_url(
    *,
    ref_id: str,
    storage_uri: str,
    secret: str,
    ttl_seconds: int = 900,
) -> str:
    expires = int(time.time()) + ttl_seconds
    msg = f"{ref_id}:{storage_uri}:{expires}"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"platform-artifact://{quote(ref_id)}?expires={expires}&sig={sig}"


def verify_download_sig(*, ref_id: str, storage_uri: str, expires: int, sig: str, secret: str) -> bool:
    if int(time.time()) > int(expires):
        return False
    msg = f"{ref_id}:{storage_uri}:{expires}"
    expected = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
