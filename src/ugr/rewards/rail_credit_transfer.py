"""Governed rail credit transfers between operators (same tenant)."""

from __future__ import annotations

import os
import time
from hashlib import sha256
from typing import Any
from uuid import uuid4

from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_credit_transfer_receipt import build_credit_transfer_receipt
from src.ugr.rewards.operator_reward_spec import (
    EVENT_RAIL_CREDITS_RECEIVED,
    EVENT_RAIL_CREDITS_SENT,
)
from src.ugr.rewards.reward_attribution import stable_json
from src.ugr.rewards.reward_issuer import (
    rewards_audit_only,
    rewards_enabled,
    rewards_shadow_only,
)
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import (
    compute_transfer_fee,
    load_reward_policy,
    max_outbound_per_day,
    max_per_transfer,
    max_spendable_credits,
    max_transfers_per_day,
    min_reputation_to_send,
    min_transfer_amount,
    transfer_cooldown_seconds,
)


UGR_RAIL_CREDIT_TRANSFER_ENABLED_ENV = "UGR_RAIL_CREDIT_TRANSFER_ENABLED"


def rail_credit_transfer_enabled() -> bool:
    raw = os.getenv(UGR_RAIL_CREDIT_TRANSFER_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _build_transfer_event_id(transfer_id: str, event_type: str, operator_id: str) -> str:
    canonical = {
        "transfer_id": transfer_id,
        "event_type": event_type,
        "operator_id": operator_id,
    }
    return sha256(stable_json(canonical).encode("utf-8")).hexdigest()


def _validate_transfer_request(
    *,
    tenant_id: str,
    from_operator_id: str,
    to_operator_id: str,
    amount: float,
    transfer_id: str | None,
    runtime_dir: str | None,
    policy: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Return rejection dict if invalid, else None."""
    if not rewards_enabled():
        return {"status": "disabled", "summary": "operator rewards disabled"}
    if not rail_credit_transfer_enabled():
        return {"status": "rejected", "summary": "rail credit transfer disabled", "reason": "transfer_disabled"}

    tenant_norm = normalize_tenant_id(tenant_id)
    sender = str(from_operator_id or "").strip()
    recipient = str(to_operator_id or "").strip()
    if not sender or not recipient:
        return {"status": "rejected", "summary": "from and to operator_id required", "reason": "invalid_operators"}
    if sender == recipient:
        return {"status": "rejected", "summary": "cannot transfer to self", "reason": "self_transfer"}

    pol = policy or load_reward_policy()
    amount_f = float(amount or 0)
    min_amt = min_transfer_amount(pol)
    if amount_f < min_amt:
        return {"status": "rejected", "summary": f"amount below minimum {min_amt}", "reason": "amount_too_small"}
    max_tx = max_per_transfer(pol)
    if amount_f > max_tx:
        return {"status": "rejected", "summary": f"amount exceeds max_per_transfer {max_tx}", "reason": "amount_too_large"}

    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    tid = str(transfer_id or "").strip()
    if tid and ledger.has_transfer(tid):
        return None

    sender_profile = ledger.load_balances(sender)
    if sender_profile.reputation_score < min_reputation_to_send(pol):
        return {
            "status": "rejected",
            "summary": "sender reputation below minimum to transfer",
            "reason": "reputation_too_low",
        }
    allowed = max_spendable_credits(
        sender_profile.reputation_score,
        sender_profile.rail_credits,
        policy=pol,
    )
    if amount_f > allowed:
        return {
            "status": "rejected",
            "summary": "transfer exceeds reputation-bounded allowance",
            "reason": "reputation_bounded_cap",
        }
    fee = compute_transfer_fee(amount_f, policy=pol)
    if sender_profile.rail_credits < amount_f + fee:
        return {
            "status": "rejected",
            "summary": "insufficient rail credits",
            "reason": "insufficient_balance",
        }
    now = time.time()
    if ledger.sum_outbound_transfers(sender, now=now) + amount_f > max_outbound_per_day(pol):
        return {"status": "rejected", "summary": "daily outbound transfer cap exceeded", "reason": "daily_cap_exceeded"}
    if ledger.count_outbound_transfers_today(sender, now=now) >= max_transfers_per_day(pol):
        return {"status": "rejected", "summary": "max transfers per day exceeded", "reason": "transfer_count_cap"}
    last_out = ledger.last_outbound_transfer_at(sender)
    cooldown = transfer_cooldown_seconds(pol)
    if last_out is not None and (now - last_out) < cooldown:
        return {"status": "rejected", "summary": "transfer cooldown active", "reason": "cooldown_active"}
    return None


def transfer_rail_credits(
    *,
    tenant_id: str,
    from_operator_id: str,
    to_operator_id: str,
    amount: float,
    trace_id: str,
    transfer_id: str | None = None,
    memo: str | None = None,
    exchange_id: str | None = None,
    runtime_dir: str | None = None,
    policy: dict[str, Any] | None = None,
    skip_balance_write: bool = False,
) -> dict[str, Any]:
    """P2P rail credit transfer with anti-gaming policy enforcement."""
    pol = policy or load_reward_policy()
    tenant_norm = normalize_tenant_id(tenant_id)
    sender = str(from_operator_id or "").strip()
    recipient = str(to_operator_id or "").strip()
    amount_f = float(amount or 0)

    rejection = _validate_transfer_request(
        tenant_id=tenant_norm,
        from_operator_id=sender,
        to_operator_id=recipient,
        amount=amount_f,
        transfer_id=transfer_id,
        runtime_dir=runtime_dir,
        policy=pol,
    )
    if rejection:
        return rejection

    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    tid = str(transfer_id or "").strip() or str(uuid4())
    if ledger.has_transfer(tid):
        return {
            "status": "idempotent",
            "summary": "transfer already recorded",
            "transfer_id": tid,
        }

    fee = compute_transfer_fee(amount_f, policy=pol)
    total_debit = amount_f + fee
    now = time.time()
    sender_profile = ledger.load_balances(sender)
    recipient_profile = ledger.load_balances(recipient)
    transfer_receipt = build_credit_transfer_receipt(
        transfer_id=tid,
        tenant_id=tenant_norm,
        from_operator_id=sender,
        to_operator_id=recipient,
        amount=amount_f,
        fee=fee,
        trace_id=str(trace_id or "").strip(),
        memo=memo,
        exchange_id=exchange_id,
        issued_at=now,
        runtime_dir=runtime_dir,
    )

    preview = {
        "status": "audit",
        "summary": "transfer validated (audit-only, no balance write)",
        "transfer_id": tid,
        "amount": amount_f,
        "fee": fee,
        "from_operator_id": sender,
        "to_operator_id": recipient,
        "credit_transfer_receipt": transfer_receipt,
        "sender_balance_preview": sender_profile.rail_credits - total_debit,
        "recipient_balance_preview": recipient_profile.rail_credits + amount_f,
    }

    if rewards_audit_only():
        return preview

    if rewards_shadow_only() or skip_balance_write:
        return {
            **preview,
            "status": "shadow",
            "summary": "transfer validated (shadow-only, no balance write)",
        }

    sender_profile.rail_credits = max(0.0, sender_profile.rail_credits - total_debit)
    sender_profile.updated_at = now
    recipient_profile.rail_credits = max(0.0, recipient_profile.rail_credits + amount_f)
    recipient_profile.updated_at = now
    ledger.save_balances(sender_profile)
    ledger.save_balances(recipient_profile)

    sent_event = {
        "event_type": EVENT_RAIL_CREDITS_SENT,
        "event_id": _build_transfer_event_id(tid, EVENT_RAIL_CREDITS_SENT, sender),
        "transfer_id": tid,
        "tenant_id": tenant_norm,
        "operator_id": sender,
        "counterparty": recipient,
        "amount": amount_f,
        "fee": fee,
        "trace_id": str(trace_id or "").strip(),
        "memo": memo,
        "exchange_id": exchange_id,
        "issued_at": now,
        "credit_transfer_receipt": transfer_receipt,
    }
    received_event = {
        "event_type": EVENT_RAIL_CREDITS_RECEIVED,
        "event_id": _build_transfer_event_id(tid, EVENT_RAIL_CREDITS_RECEIVED, recipient),
        "transfer_id": tid,
        "tenant_id": tenant_norm,
        "operator_id": recipient,
        "counterparty": sender,
        "amount": amount_f,
        "fee": 0.0,
        "trace_id": str(trace_id or "").strip(),
        "memo": memo,
        "exchange_id": exchange_id,
        "issued_at": now,
        "credit_transfer_receipt": transfer_receipt,
    }
    ledger.append_event(sent_event)
    ledger.append_event(received_event)

    return {
        "status": "ok",
        "summary": "rail credits transferred",
        "transfer_id": tid,
        "amount": amount_f,
        "fee": fee,
        "from_operator_id": sender,
        "to_operator_id": recipient,
        "credit_transfer_receipt": transfer_receipt,
        "sender_profile": sender_profile.to_dict(),
        "recipient_profile": recipient_profile.to_dict(),
    }


def exchange_rail_credits(
    *,
    tenant_id: str,
    operator_a: str,
    operator_b: str,
    amount_a: float,
    amount_b: float,
    trace_id: str,
    exchange_id: str | None = None,
    runtime_dir: str | None = None,
) -> dict[str, Any]:
    """Atomic two-way rail credit exchange between two operators."""
    op_a = str(operator_a or "").strip()
    op_b = str(operator_b or "").strip()
    if not op_a or not op_b:
        return {"status": "rejected", "summary": "operator_a and operator_b required"}
    if op_a == op_b:
        return {"status": "rejected", "summary": "operators must differ", "reason": "self_exchange"}
    amt_a = float(amount_a or 0)
    amt_b = float(amount_b or 0)
    if amt_a <= 0 and amt_b <= 0:
        return {"status": "rejected", "summary": "at least one leg amount must be positive"}

    eid = str(exchange_id or "").strip() or f"exch-{uuid4()}"
    pol = load_reward_policy()
    if amt_a > 0:
        err = _validate_transfer_request(
            tenant_id=tenant_id,
            from_operator_id=op_a,
            to_operator_id=op_b,
            amount=amt_a,
            transfer_id=f"{eid}:a-to-b",
            runtime_dir=runtime_dir,
            policy=pol,
        )
        if err:
            return {**err, "leg": "a_to_b"}
    if amt_b > 0:
        err = _validate_transfer_request(
            tenant_id=tenant_id,
            from_operator_id=op_b,
            to_operator_id=op_a,
            amount=amt_b,
            transfer_id=f"{eid}:b-to-a",
            runtime_dir=runtime_dir,
            policy=pol,
        )
        if err:
            return {**err, "leg": "b_to_a"}

    legs: list[dict[str, Any]] = []

    if amt_a > 0:
        result_ab = transfer_rail_credits(
            tenant_id=tenant_id,
            from_operator_id=op_a,
            to_operator_id=op_b,
            amount=amt_a,
            trace_id=trace_id,
            transfer_id=f"{eid}:a-to-b",
            exchange_id=eid,
            runtime_dir=runtime_dir,
        )
        if str(result_ab.get("status") or "") not in {"ok", "shadow", "audit", "idempotent"}:
            return {
                "status": "rejected",
                "summary": f"exchange leg a→b failed: {result_ab.get('summary')}",
                "reason": result_ab.get("reason"),
                "leg": "a_to_b",
                "leg_result": result_ab,
            }
        legs.append(result_ab)

    if amt_b > 0:
        result_ba = transfer_rail_credits(
            tenant_id=tenant_id,
            from_operator_id=op_b,
            to_operator_id=op_a,
            amount=amt_b,
            trace_id=trace_id,
            transfer_id=f"{eid}:b-to-a",
            exchange_id=eid,
            runtime_dir=runtime_dir,
        )
        if str(result_ba.get("status") or "") not in {"ok", "shadow", "audit", "idempotent"}:
            return {
                "status": "rejected",
                "summary": f"exchange leg b→a failed: {result_ba.get('summary')}",
                "reason": result_ba.get("reason"),
                "leg": "b_to_a",
                "leg_result": result_ba,
                "completed_legs": legs,
            }
        legs.append(result_ba)

    statuses = {str(leg.get("status") or "") for leg in legs}
    overall = "ok" if statuses <= {"ok"} else (statuses.pop() if len(statuses) == 1 else "ok")
    return {
        "status": overall,
        "summary": "rail credit exchange completed",
        "exchange_id": eid,
        "legs": legs,
    }
