from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from nova.node.identity import NodeIdentity
from nova.node.ledger import append_jsonl, read_jsonl, runtime_dir, stable_hash


class NodeVeto(Exception):
    def __init__(self, *, reason: str, policy_version: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.policy_version = policy_version


class GovernanceRuntime:
    def __init__(self, policy_path: str = "./policy.yaml") -> None:
        self.policy_path = policy_path
        self.policy = self.load_policy()

    def load_policy(self) -> dict[str, Any]:
        policy_file = Path(self.policy_path)
        if policy_file.exists():
            return _load_policy_file(policy_file)
        return default_policy()

    def continuity_receipt(self) -> dict[str, Any]:
        return {
            "trace_id": f"trace-{uuid4()}",
            "timestamp": int(time.time()),
            "policy_version": self.policy.get("version", "1.0"),
        }

    def enforce_invariants(self, payload: dict[str, Any]) -> dict[str, Any]:
        receipts: list[str] = []
        boundedness = self.policy.get("invariants", {}).get("boundedness", {})
        max_payload_bytes = _env_int(
            "NOVA_NODE_MAX_PAYLOAD_BYTES",
            int(boundedness.get("max_payload_bytes", 500000)),
        )
        if len(json.dumps(payload, sort_keys=True).encode("utf-8")) > max_payload_bytes:
            return {
                "decision": "blocked",
                "reason": "payload-too-large",
                **self.continuity_receipt(),
            }
        max_tokens = _env_int("NOVA_NODE_MAX_TOKENS", int(boundedness.get("max_tokens", 2048)))
        if int(payload.get("max_tokens") or 0) > max_tokens:
            return {
                "decision": "blocked",
                "reason": "token-limit-exceeded",
                **self.continuity_receipt(),
            }
        receipts.append("boundedness")

        banned = self.policy.get("safety", {}).get("banned_intents", [])
        if payload.get("intent") in banned:
            return {
                "decision": "blocked",
                "reason": "banned-intent",
                **self.continuity_receipt(),
            }

        rate_decision = _enforce_rate_limits(payload, self.policy)
        if rate_decision:
            return {
                **rate_decision,
                **self.continuity_receipt(),
            }
        receipts.append("rate-limit")

        receipts.extend(["continuity", "provenance", "veto"])
        return {
            "decision": "allowed",
            "receipts": receipts,
            **self.continuity_receipt(),
        }


def load_node_policy(policy_path: str = "./policy.yaml") -> dict[str, Any]:
    policy = GovernanceRuntime(policy_path).policy
    ident = NodeIdentity.load(policy_path)
    base_policy = {
        "node_id": ident.node_id,
        "operator_id": ident.operator_id,
        "operator_key_id": ident.operator_key_id,
        "policy_version": str(policy.get("version", "1.0")),
        "policy_hash": ident.policy_hash,
        "conformance_profile": str(policy.get("conformance_profile", os.environ.get("NOVA_NODE_CONFORMANCE", "N0"))),
        "max_payload_bytes": int(
            _env_int(
                "NOVA_NODE_MAX_PAYLOAD_BYTES",
                int(policy.get("invariants", {}).get("boundedness", {}).get("max_payload_bytes", 500000)),
            )
        ),
    }
    if not Path(policy_path).exists():
        base_policy["policy_hash"] = stable_hash(base_policy)[7:]
    return base_policy


def default_policy() -> dict[str, Any]:
    return {
        "version": os.environ.get("NOVA_NODE_POLICY_VERSION", "1.0"),
        "conformance_profile": os.environ.get("NOVA_NODE_CONFORMANCE", "N0"),
        "invariants": {
            "boundedness": {
                "enforce": True,
                "max_tokens": _env_int("NOVA_NODE_MAX_TOKENS", 2048),
                "max_payload_bytes": _env_int("NOVA_NODE_MAX_PAYLOAD_BYTES", 500000),
            }
        },
        "safety": {
            "banned_intents": [],
            "rate_limits": {
                "per_user_per_minute": _env_int("NOVA_NODE_RATE_PER_MINUTE", 10),
                "per_user_per_hour": _env_int("NOVA_NODE_RATE_PER_HOUR", 200),
            },
        },
    }


def get_rate_limit_state(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    active_policy = policy or GovernanceRuntime().policy
    limits = _rate_limits(active_policy)
    now = int(time.time())
    minute_bucket = now // 60
    hour_bucket = now // 3600
    callers: dict[str, dict[str, int]] = {}
    for event in read_jsonl(_rate_limit_path()):
        caller = str(event.get("caller_id") or "unknown")
        info = callers.setdefault(caller, {"minute_count": 0, "hour_count": 0, "blocked_count": 0})
        if event.get("minute_bucket") == minute_bucket:
            info["minute_count"] += 1
        if event.get("hour_bucket") == hour_bucket:
            info["hour_count"] += 1
        if event.get("blocked"):
            info["blocked_count"] += 1
    return {"limits": limits, "callers": callers}


def _load_policy_file(policy_file: Path) -> dict[str, Any]:
    text = policy_file.read_text(encoding="utf-8")
    try:
        import yaml

        data = yaml.safe_load(text)
        return data or {}
    except Exception:
        return json.loads(text)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _enforce_rate_limits(payload: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any] | None:
    limits = _rate_limits(policy)
    caller_id = str(payload.get("caller_id") or payload.get("user") or "anonymous")
    now = int(time.time())
    minute_bucket = now // 60
    hour_bucket = now // 3600
    current = get_rate_limit_state(policy).get("callers", {}).get(caller_id, {})
    blocked = (
        current.get("minute_count", 0) >= limits["per_user_per_minute"]
        or current.get("hour_count", 0) >= limits["per_user_per_hour"]
    )
    append_jsonl(
        _rate_limit_path(),
        {
            "timestamp": now,
            "caller_id": caller_id,
            "minute_bucket": minute_bucket,
            "hour_bucket": hour_bucket,
            "blocked": blocked,
        },
    )
    if not blocked:
        return None
    return {
        "decision": "blocked",
        "reason": "rate-limit-exceeded",
        "rate_limit": limits,
    }


def _rate_limits(policy: dict[str, Any]) -> dict[str, int]:
    configured = policy.get("safety", {}).get("rate_limits", {})
    return {
        "per_user_per_minute": _env_int(
            "NOVA_NODE_RATE_PER_MINUTE",
            int(configured.get("per_user_per_minute", 10)),
        ),
        "per_user_per_hour": _env_int(
            "NOVA_NODE_RATE_PER_HOUR",
            int(configured.get("per_user_per_hour", 200)),
        ),
    }


def _rate_limit_path() -> Path:
    return runtime_dir() / "rate-limits.jsonl"
