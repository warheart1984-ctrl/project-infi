"""Rail credit spend — debit balance and issue forge boost token."""

from __future__ import annotations

import os
import time
from hashlib import sha256
from typing import Any
from uuid import uuid4

from src.ugr.rewards.reward_attribution import stable_json
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import (
    load_reward_policy,
    max_spendable_credits,
    min_reputation_to_spend,
)


UGR_RAIL_CREDIT_SPEND_ENABLED_ENV = "UGR_RAIL_CREDIT_SPEND_ENABLED"


def rail_credit_spend_enabled() -> bool:
    raw = os.getenv(UGR_RAIL_CREDIT_SPEND_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def spend_rail_credits(
    *,
    tenant_id: str,
    operator_id: str,
    amount: float,
    trace_id: str,
    purpose: str = "express_boost",
    runtime_dir: str | None = None,
) -> dict[str, Any]:
    if not rail_credit_spend_enabled():
        return {"status": "rejected", "summary": "rail credit spend disabled"}

    policy = load_reward_policy()
    spend_policy = dict((policy.get("spend") or {}).get("express_boost") or {})
    if purpose != "express_boost":
        return {"status": "rejected", "summary": f"unsupported spend purpose: {purpose}"}

    amount_f = float(amount or 0)
    if amount_f <= 0:
        return {"status": "rejected", "summary": "amount must be positive"}
    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_id)
    profile = ledger.load_balances(operator_id)

    min_rep = min_reputation_to_spend(policy)
    if profile.reputation_score < min_rep:
        return {
            "status": "rejected",
            "summary": f"reputation {profile.reputation_score} below minimum {min_rep} to spend credits",
            "reputation_score": profile.reputation_score,
            "economy": "reputation_primary",
        }

    allowed = max_spendable_credits(profile.reputation_score, profile.rail_credits, policy=policy)
    if amount_f > allowed:
        return {
            "status": "rejected",
            "summary": "spend exceeds reputation-bounded allowance",
            "max_spendable": allowed,
            "balance": profile.rail_credits,
            "reputation_score": profile.reputation_score,
        }

    if profile.rail_credits < amount_f:
        return {
            "status": "rejected",
            "summary": "insufficient rail credits",
            "balance": profile.rail_credits,
        }

    credits_per_point = float(spend_policy.get("credits_per_point") or 1)
    max_reduction = float(spend_policy.get("max_threshold_reduction") or 30)
    ttl_seconds = int(spend_policy.get("ttl_seconds") or 300)
    threshold_reduction = min(max_reduction, amount_f / max(credits_per_point, 0.001))

    spend_id = str(uuid4())
    issued_at = time.time()
    expires_at = issued_at + ttl_seconds
    forge_boost = {
        "spend_id": spend_id,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "trace_id": str(trace_id or "").strip(),
        "purpose": purpose,
        "amount": amount_f,
        "threshold_reduction": threshold_reduction,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    canonical = stable_json(
        {
            "spend_id": spend_id,
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "amount": amount_f,
            "threshold_reduction": threshold_reduction,
            "expires_at": expires_at,
        }
    )
    forge_boost["spend_digest"] = sha256(canonical.encode("utf-8")).hexdigest()

    profile.rail_credits = max(0.0, profile.rail_credits - amount_f)
    profile.updated_at = issued_at
    ledger.save_balances(profile)
    ledger.save_spend_token(
        spend_id,
        {
            **forge_boost,
            "consumed": False,
        },
    )

    spend_receipt = {
        "spend_id": spend_id,
        "operator_id": operator_id,
        "tenant_id": tenant_id,
        "amount": amount_f,
        "balance_after": profile.rail_credits,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }

    return {
        "status": "ok",
        "summary": "rail credits spent",
        "spend_receipt": spend_receipt,
        "forge_boost": forge_boost,
        "profile": profile.to_dict(),
    }


def validate_forge_boost(boost: dict[str, Any] | None, *, runtime_dir: str | None = None) -> tuple[bool, str, dict[str, Any]]:
    if not boost:
        return False, "no boost", {}
    spend_id = str(boost.get("spend_id") or "").strip()
    if not spend_id:
        return False, "missing spend_id", {}
    ledger = RewardLedger(
        runtime_dir=runtime_dir,
        tenant_id=str(boost.get("tenant_id") or "global"),
    )
    token = ledger.load_spend_token(spend_id)
    if not token:
        return False, "unknown spend token", {}
    if token.get("consumed"):
        return False, "spend token already consumed", {}
    if time.time() > float(token.get("expires_at") or 0):
        return False, "spend token expired", {}
    digest = str(boost.get("spend_digest") or "")
    if digest != str(token.get("spend_digest") or ""):
        return False, "spend digest mismatch", {}
    return True, "ok", token


def consume_forge_boost(boost: dict[str, Any] | None, *, runtime_dir: str | None = None) -> None:
    spend_id = str((boost or {}).get("spend_id") or "").strip()
    if not spend_id:
        return
    ledger = RewardLedger(
        runtime_dir=runtime_dir,
        tenant_id=str((boost or {}).get("tenant_id") or "global"),
    )
    ledger.mark_spend_consumed(spend_id)
