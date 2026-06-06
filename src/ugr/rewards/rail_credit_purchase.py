"""Rail credit purchase — ledger-only mint after off-platform payment."""

from __future__ import annotations

import os
import time
from hashlib import sha256
from typing import Any
from uuid import uuid4

from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_reward_spec import EVENT_RAIL_CREDITS_PURCHASED
from src.ugr.rewards.purchase_receipt import build_purchase_receipt, verify_purchase_receipt
from src.ugr.rewards.reward_attribution import stable_json
from src.ugr.rewards.reward_issuer import rewards_audit_only, rewards_enabled, rewards_shadow_only
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import (
    load_reward_policy,
    max_per_purchase,
    max_purchase_per_operator_per_day,
    purchase_enabled,
)


UGR_RAIL_CREDIT_PURCHASE_ENABLED_ENV = "UGR_RAIL_CREDIT_PURCHASE_ENABLED"


def rail_credit_purchase_enabled() -> bool:
    raw = os.getenv(UGR_RAIL_CREDIT_PURCHASE_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def purchase_rail_credits(
    *,
    tenant_id: str,
    operator_id: str,
    amount: float,
    payment_reference: str,
    trace_id: str,
    purchase_receipt: dict[str, Any] | None = None,
    runtime_dir: str | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not rewards_enabled():
        return {"status": "disabled", "summary": "operator rewards disabled"}
    if not rail_credit_purchase_enabled():
        return {"status": "rejected", "summary": "rail credit purchase disabled"}

    pol = policy or load_reward_policy()
    if not purchase_enabled(pol):
        return {"status": "rejected", "summary": "purchase disabled by policy"}

    tenant_norm = normalize_tenant_id(tenant_id)
    op = str(operator_id or "").strip()
    amount_f = float(amount or 0)
    if amount_f <= 0:
        return {"status": "rejected", "summary": "amount must be positive"}
    if amount_f > max_per_purchase(pol):
        return {
            "status": "rejected",
            "summary": "amount exceeds max_per_purchase",
            "max_per_purchase": max_per_purchase(pol),
        }

    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    profile = ledger.load_balances(op)
    daily_total = ledger.sum_purchases_today(op)
    daily_cap = max_purchase_per_operator_per_day(pol)
    if daily_total + amount_f > daily_cap:
        return {
            "status": "rejected",
            "summary": "daily purchase cap exceeded",
            "daily_total": daily_total,
            "daily_cap": daily_cap,
        }

    receipt = dict(purchase_receipt or {})
    if not receipt:
        receipt = build_purchase_receipt(
            tenant_id=tenant_norm,
            operator_id=op,
            amount=amount_f,
            payment_reference=payment_reference,
            runtime_dir=runtime_dir,
        )
    ok, reason = verify_purchase_receipt(receipt, runtime_dir=runtime_dir)
    if not ok:
        return {"status": "rejected", "summary": f"invalid purchase receipt: {reason}"}

    purchase_id = str(receipt.get("purchase_id") or "").strip()
    if normalize_tenant_id(receipt.get("tenant_id")) != tenant_norm:
        return {"status": "rejected", "summary": "tenant mismatch on purchase receipt"}
    if str(receipt.get("operator_id") or "").strip() != op:
        return {"status": "rejected", "summary": "operator mismatch on purchase receipt"}
    if float(receipt.get("amount") or 0) != amount_f:
        return {"status": "rejected", "summary": "amount mismatch on purchase receipt"}

    event_id = sha256(
        stable_json(
            {
                "event_type": EVENT_RAIL_CREDITS_PURCHASED,
                "purchase_id": purchase_id,
                "operator_id": op,
                "tenant_id": tenant_norm,
            }
        ).encode("utf-8")
    ).hexdigest()

    if ledger.has_event(event_id):
        return {
            "status": "idempotent",
            "summary": "purchase already recorded",
            "purchase_id": purchase_id,
            "profile": profile.to_dict(),
        }

    preview = {
        "status": "audit",
        "summary": "purchase computed (audit-only)",
        "purchase_id": purchase_id,
        "amount": amount_f,
        "profile_preview": profile.to_dict(),
    }
    if rewards_audit_only():
        return preview
    if rewards_shadow_only():
        return {**preview, "status": "shadow", "summary": "purchase validated (shadow-only)"}

    issued_at = time.time()
    profile.apply_deltas(
        purchased_rail_credits=amount_f,
        issued_at=issued_at,
    )
    ledger.save_balances(profile)

    record = {
        "event_id": event_id,
        "event_type": EVENT_RAIL_CREDITS_PURCHASED,
        "operator_id": op,
        "tenant_id": tenant_norm,
        "amount": amount_f,
        "trace_id": str(trace_id or "").strip(),
        "purchase_id": purchase_id,
        "payment_reference": receipt.get("payment_reference"),
        "credit_source": "purchased",
        "deltas": {"purchased_rail_credits": amount_f},
        "purchase_receipt": receipt,
        "issued_at": issued_at,
    }
    ledger.append_event(record)

    return {
        "status": "ok",
        "summary": "rail credits purchased",
        "purchase_id": purchase_id,
        "amount": amount_f,
        "purchase_receipt": receipt,
        "profile": profile.to_dict(),
    }
