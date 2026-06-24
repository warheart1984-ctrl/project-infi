"""CRK-1 Governance Receipt Merkleizer — tamper-evident audit spine."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def json_dumps_canonical(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_receipt(receipt: dict[str, Any]) -> str:
    """SHA-256 over canonical JSON encoding of a governance receipt."""
    payload = json_dumps_canonical(receipt).encode("utf-8")
    return _hash_bytes(payload)


def merkle_root(receipts: list[dict[str, Any]]) -> str:
    """
    Compute Merkle root over governance receipts.
    Each leaf = SHA256(canonical_json(receipt)).
    """
    if not receipts:
        return _hash_bytes(b"")

    layer = [bytes.fromhex(hash_receipt(receipt)) for receipt in receipts]

    while len(layer) > 1:
        next_layer: list[bytes] = []
        for index in range(0, len(layer), 2):
            left = layer[index]
            right = layer[index + 1] if index + 1 < len(layer) else left
            next_layer.append(hashlib.sha256(left + right).digest())
        layer = next_layer

    return layer[0].hex()


def audit_spine(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Summary block suitable for Kernel / Mutation ledger attachment."""
    return {
        "receipt_count": len(receipts),
        "merkle_root": merkle_root(receipts),
        "leaf_hashes": [hash_receipt(receipt) for receipt in receipts],
    }
