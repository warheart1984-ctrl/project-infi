"""Canonical JSON hashing — stdlib only, no founder dependencies."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_hash(canonical: dict[str, Any]) -> str:
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_event_hash(event: dict[str, Any]) -> str:
    raw = {
        "id": event["id"],
        "actor_id": event["actor_id"],
        "action_type": event["action_type"],
        "action_payload": event["action_payload"],
        "location": event["location"],
        "timestamp": event["timestamp"],
    }
    return compute_hash(raw)


def canonical_package_payload(artifacts: dict[str, Any]) -> dict[str, Any]:
    event = artifacts["event"]
    memory = artifacts["memory"]
    claim = artifacts["derived_claim"]
    verification = artifacts["verification"]
    return {
        "event_id": event["id"],
        "event_hash": memory["event_hash"],
        "replay_state": artifacts["replay_state"]["state"],
        "claim_id": claim["id"],
        "claim_type": claim["claim_type"],
        "claim_location": claim["location"],
        "claim_summary": claim["summary"],
        "verification_status": verification["status"],
        "verification_method": verification["method"],
    }


def compute_package_hash(artifacts: dict[str, Any]) -> str:
    return compute_hash(canonical_package_payload(artifacts))
