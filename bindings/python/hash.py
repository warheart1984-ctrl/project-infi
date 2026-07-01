"""CAS receipt canonical JSON + SHA-256 (Python side of cross-language contract)."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Canonical form: JSON with sorted keys, compact separators, UTF-8."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def hash_receipt_dict(receipt: dict) -> str:
    """SHA-256(canonical_json_bytes). Clears `hash` before hashing."""
    payload = dict(receipt)
    payload["hash"] = ""
    canonical = canonical_json(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
