"""Merkle root over governed mission transitions."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash_pair(left: str, right: str) -> str:
    combined = f"{left}{right}".encode("utf-8")
    return sha256(combined).hexdigest()


def transition_leaf_hash(transition: dict[str, Any]) -> str:
    """Single transition leaf = SHA256(canonical transition)."""
    return sha256(_stable_json(transition).encode("utf-8")).hexdigest()


def compute_ledger_merkle_root(transitions: list[dict[str, Any]]) -> str:
    """
    Binary Merkle root over sorted governed transitions.

    Empty ledger returns SHA256 of empty string (documented sentinel).
    """
    if not transitions:
        return sha256(b"").hexdigest()

    sorted_rows = sorted(transitions, key=lambda row: str(row.get("action_id") or ""))
    level = [transition_leaf_hash(row) for row in sorted_rows]

    while len(level) > 1:
        next_level: list[str] = []
        for index in range(0, len(level), 2):
            left = level[index]
            right = level[index + 1] if index + 1 < len(level) else left
            next_level.append(_hash_pair(left, right))
        level = next_level

    return level[0]
