"""Shared hashing utilities for continuity-sdk experiments."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(payload: str | bytes | dict[str, Any]) -> str:
    if isinstance(payload, dict):
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    elif isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = payload
    return hashlib.sha256(body).hexdigest()
