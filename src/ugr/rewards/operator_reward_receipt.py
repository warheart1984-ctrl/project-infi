"""Operator reward receipt v1 — signed proof of incentive event."""

from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from src.ugr.mission.receipt_signing import load_urg_receipt_signing_key, sign_urg_receipt
from src.ugr.rewards.reward_events import stable_json


REWARD_RECEIPT_SCHEMA_VERSION = "1.0"


def build_operator_reward_receipt(
    event: dict[str, Any],
    profile: dict[str, Any],
    *,
    runtime_dir: str | None = None,
    create_key_if_missing: bool = True,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "receipt_schema_version": REWARD_RECEIPT_SCHEMA_VERSION,
        "receipt_id": str(uuid4()),
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "operator_id": event.get("operator_id"),
        "tenant_id": event.get("tenant_id"),
        "subsystem_id": event.get("subsystem_id"),
        "discovery_receipt_id": event.get("discovery_receipt_id"),
        "governance_mission_id": event.get("governance_mission_id"),
        "promotion_organ_id": event.get("promotion_organ_id"),
        "deltas": dict(event.get("deltas") or {}),
        "attribution": dict(event.get("attribution") or {}),
        "profile_snapshot": {
            "reputation_score": profile.get("reputation_score"),
            "rail_credits": profile.get("rail_credits"),
            "adoption_multipliers": dict(profile.get("adoption_multipliers") or {}),
        },
        "issued_at": event.get("issued_at") or time.time(),
    }
    _, urg_key_id = load_urg_receipt_signing_key(
        runtime_dir=runtime_dir,
        create_if_missing=create_key_if_missing,
    )
    if urg_key_id:
        receipt["urg_key_id"] = urg_key_id
    receipt_sig, algorithm, _ = sign_urg_receipt(
        receipt,
        runtime_dir=runtime_dir,
        create_key_if_missing=create_key_if_missing,
    )
    receipt["receipt_sig"] = receipt_sig
    receipt["receipt_algorithm"] = algorithm
    return receipt


def verify_operator_reward_receipt(
    receipt: dict[str, Any],
    *,
    runtime_dir: str | None = None,
) -> tuple[bool, str]:
    from hashlib import sha256
    import hmac

    from src.ugr.mission.receipt_signing import (
        ALGORITHM_CONTENT_ONLY,
        ALGORITHM_HMAC,
        build_urg_receipt_canonical,
        load_urg_receipt_signing_key,
    )

    canonical = stable_json(build_urg_receipt_canonical(receipt))
    sig = str(receipt.get("receipt_sig") or "")
    algorithm = str(receipt.get("receipt_algorithm") or ALGORITHM_CONTENT_ONLY)
    key, _ = load_urg_receipt_signing_key(runtime_dir=runtime_dir, create_if_missing=False)
    if algorithm == ALGORITHM_HMAC and key:
        expected = hmac.new(key.encode("utf-8"), canonical.encode("utf-8"), sha256).hexdigest()
        if hmac.compare_digest(expected, sig):
            return True, "ok"
        return False, "receipt_sig mismatch"
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if hmac.compare_digest(expected, sig):
        return True, "ok"
    return False, "receipt_sig mismatch"
