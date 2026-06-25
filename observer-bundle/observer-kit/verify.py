"""Package verification and RP-1.0 reproduction — pure functions."""

from __future__ import annotations

from typing import Any

from canonical import compute_event_hash, compute_package_hash
from replay import replay_events


def verify_claim_by_replay(artifacts: dict[str, Any]) -> dict[str, Any]:
    claim = artifacts["derived_claim"]
    event = artifacts["event"]
    state = replay_events([event])
    location = claim["location"]
    flags = state.get("locations", {}).get(location, {}).get("flags", {})
    if claim["claim_type"] == "boss_defeated" and flags.get("boss_defeated") is True:
        return {"status": "verified", "location": location}
    return {"status": "failed", "location": location, "flags": flags}


def verify_package(package: dict[str, Any]) -> dict[str, Any]:
    artifacts = package["artifacts"]
    expected_hash = package["canonical_hash"]
    recomputed = compute_package_hash(artifacts)
    event = artifacts["event"]
    memory = artifacts["memory"]
    event_hash_ok = memory["event_hash"] == compute_event_hash(event)
    replay = replay_events([event])
    state_ok = replay == artifacts["replay_state"]["state"]
    claim = verify_claim_by_replay(artifacts)
    hash_ok = recomputed == expected_hash
    verified = hash_ok and event_hash_ok and state_ok and claim["status"] == "verified"
    return {
        "status": "verified" if verified else "failed",
        "canonical_hash": expected_hash if verified else recomputed,
        "canonical_hash_match": hash_ok,
        "event_hash_match": event_hash_ok,
        "replay_state_match": state_ok,
        "claim_verification": claim,
        "recomputed_hash": recomputed,
    }


def reproduce_package(package: dict[str, Any], *, observer: str = "Observer-01") -> dict[str, Any]:
    result = verify_package(package)
    return {
        "protocol": "RP-1.0",
        "observer": observer,
        "package_id": package.get("id"),
        "result": result["status"],
        "details": result,
    }
