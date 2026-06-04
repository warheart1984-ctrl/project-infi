"""Load operator reward policy — reputation-primary governed economy."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_POLICY: dict[str, Any] = {
    "version": "1.1",
    "economy": {
        "reputation_primary": True,
        "reputation_to_credit_ratio_min": 2.0,
        "credit_earn_cap_fraction_of_reputation": 0.35,
        "min_reputation_to_spend_credits": 10,
        "max_spend_per_reputation_point": 0.15,
    },
    "discovery": {
        "reputation": 15,
        "rail_credits": 3,
        "search_efficiency_bonus": {"max_attempts": 8, "reputation": 3, "rail_credits": 0},
    },
    "promotion": {"reputation": 40, "rail_credits": 8},
    "adoption": {
        "reputation": 10,
        "rail_credits": 0,
        "multiplier_increment": 0.1,
        "multiplier_cap": 3.0,
        "reputation_scales_with_multiplier": True,
    },
    "spend": {
        "express_boost": {
            "credits_per_point": 1,
            "max_threshold_reduction": 30,
            "ttl_seconds": 300,
        }
    },
    "transfer": {
        "min_reputation_to_send": 10,
        "max_per_transfer": 25,
        "max_outbound_per_day": 50,
        "max_transfers_per_day": 20,
        "transfer_fee_fraction": 0.02,
        "min_amount": 0.01,
        "cooldown_seconds": 30,
    },
}

LIFECYCLE_CHAIN = (
    "discovery",
    "proof",
    "receipt",
    "governance",
    "promotion",
    "adoption",
    "attribution",
    "reward",
)


def _default_policy_path() -> Path:
    env_path = os.getenv("UGR_REWARD_POLICY_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "reward-policy.json"


_policy_cache: dict[str, Any] | None = None


def invalidate_reward_policy_cache() -> None:
    global _policy_cache
    _policy_cache = None


def load_reward_policy(path: str | Path | None = None) -> dict[str, Any]:
    global _policy_cache
    if path is None and _policy_cache is not None:
        return dict(_policy_cache)

    policy_path = Path(path) if path else _default_policy_path()
    if not policy_path.exists():
        merged = dict(DEFAULT_POLICY)
    else:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
        merged = dict(DEFAULT_POLICY)
        merged.update({k: v for k, v in payload.items() if k != "economy"})
        if isinstance(payload.get("economy"), dict):
            merged["economy"] = {**dict(DEFAULT_POLICY.get("economy") or {}), **payload["economy"]}
        for key in ("discovery", "promotion", "adoption", "spend", "transfer"):
            if key in payload and isinstance(payload[key], dict):
                merged[key] = {**dict(DEFAULT_POLICY.get(key) or {}), **payload[key]}
    if path is None:
        _policy_cache = dict(merged)
    return merged


def economy_policy(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict((policy or load_reward_policy()).get("economy") or DEFAULT_POLICY["economy"])


def cap_rail_credit_earn(
    reputation_delta: float,
    base_credits: float,
    *,
    profile_reputation: float = 0,
    policy: dict[str, Any] | None = None,
) -> float:
    """Credits are utility-only: earn is capped relative to verified reputation contribution."""
    econ = economy_policy(policy)
    if not econ.get("reputation_primary", True):
        return max(0.0, base_credits)
    ratio = float(econ.get("reputation_to_credit_ratio_min") or 2.0)
    cap_frac = float(econ.get("credit_earn_cap_fraction_of_reputation") or 0.35)
    if reputation_delta <= 0:
        return 0.0
    by_ratio = reputation_delta / max(ratio, 0.01)
    by_profile = (profile_reputation + reputation_delta) * cap_frac
    return max(0.0, min(base_credits, by_ratio, by_profile))


def max_spendable_credits(
    profile_reputation: float,
    balance: float,
    *,
    policy: dict[str, Any] | None = None,
) -> float:
    """Spend cannot outpace standing — bounded by reputation and balance."""
    econ = economy_policy(policy)
    per_point = float(econ.get("max_spend_per_reputation_point") or 0.15)
    rep_cap = profile_reputation * per_point
    return max(0.0, min(balance, rep_cap))


def min_reputation_to_spend(policy: dict[str, Any] | None = None) -> float:
    return float(economy_policy(policy).get("min_reputation_to_spend_credits") or 10)


def transfer_policy(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    return dict((policy or load_reward_policy()).get("transfer") or DEFAULT_POLICY["transfer"])


def min_reputation_to_send(policy: dict[str, Any] | None = None) -> float:
    tp = transfer_policy(policy)
    spend_min = min_reputation_to_spend(policy)
    return max(float(tp.get("min_reputation_to_send") or spend_min), spend_min)


def max_per_transfer(policy: dict[str, Any] | None = None) -> float:
    return float(transfer_policy(policy).get("max_per_transfer") or 25)


def max_outbound_per_day(policy: dict[str, Any] | None = None) -> float:
    return float(transfer_policy(policy).get("max_outbound_per_day") or 50)


def max_transfers_per_day(policy: dict[str, Any] | None = None) -> int:
    return int(transfer_policy(policy).get("max_transfers_per_day") or 20)


def transfer_fee_fraction(policy: dict[str, Any] | None = None) -> float:
    return max(0.0, float(transfer_policy(policy).get("transfer_fee_fraction") or 0))


def min_transfer_amount(policy: dict[str, Any] | None = None) -> float:
    return float(transfer_policy(policy).get("min_amount") or 0.01)


def transfer_cooldown_seconds(policy: dict[str, Any] | None = None) -> int:
    return int(transfer_policy(policy).get("cooldown_seconds") or 30)


def compute_transfer_fee(amount: float, *, policy: dict[str, Any] | None = None) -> float:
    frac = transfer_fee_fraction(policy)
    if frac <= 0:
        return 0.0
    return max(0.0, float(amount) * frac)
