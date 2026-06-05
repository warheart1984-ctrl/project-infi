"""Single issue_reward entry — discovery receipt gate before any ledger write."""

# Engineering: RewardIssuerEngine
from __future__ import annotations

import os
from typing import Any

from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_reward_receipt import build_operator_reward_receipt
from src.ugr.rewards.operator_reward_spec import get_event_spec
from src.ugr.rewards.reward_attribution import build_reward_event, resolve_valid_discovery_receipt
from src.ugr.rewards.reward_calculator import compute_deltas
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import load_reward_policy


UGR_OPERATOR_REWARDS_ENABLED_ENV = "UGR_OPERATOR_REWARDS_ENABLED"
UGR_REWARDS_SHADOW_ONLY_ENV = "UGR_REWARDS_SHADOW_ONLY"
UGR_REWARDS_AUDIT_ONLY_ENV = "UGR_REWARDS_AUDIT_ONLY"


def rewards_enabled() -> bool:
    raw = os.getenv(UGR_OPERATOR_REWARDS_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def rewards_shadow_only() -> bool:
    raw = os.getenv(UGR_REWARDS_SHADOW_ONLY_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def rewards_audit_only() -> bool:
    raw = os.getenv(UGR_REWARDS_AUDIT_ONLY_ENV, "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def issue_reward(
    *,
    tenant_id: str,
    operator_id: str,
    subsystem_id: str,
    event_type: str,
    discovery_receipt_id: str | None = None,
    governance_mission_id: str | None = None,
    promotion_organ_id: str | None = None,
    governance_status: str | None = None,
    runtime_dir: str | None = None,
    policy: dict[str, Any] | None = None,
    skip_if_exists: bool = True,
) -> dict[str, Any]:
    """Fail-closed reward issuance — valid discovery receipt required."""
    if not rewards_enabled():
        return {"status": "disabled", "summary": "operator rewards disabled"}

    tenant_norm = normalize_tenant_id(tenant_id)
    spec = get_event_spec(event_type)
    if spec is None:
        return {"status": "rejected", "summary": f"unknown event_type: {event_type}"}

    request_payload = {
        "tenant_id": tenant_norm,
        "operator_id": operator_id,
        "subsystem_id": subsystem_id,
        "governance_mission_id": governance_mission_id,
        "promotion_organ_id": promotion_organ_id,
    }
    spec_errors = spec.validate_request(request_payload)
    if spec_errors:
        return {"status": "rejected", "summary": "; ".join(spec_errors)}

    discovery_receipt, gate_reason = resolve_valid_discovery_receipt(
        tenant_id=tenant_norm,
        subsystem_id=subsystem_id,
        discovery_receipt_id=discovery_receipt_id,
        runtime_dir=runtime_dir,
    )
    if discovery_receipt is None:
        return {
            "status": "rejected",
            "summary": gate_reason,
            "reason": "discovery_receipt_unresolved",
        }

    pol = policy or load_reward_policy()
    ledger = RewardLedger(runtime_dir=runtime_dir, tenant_id=tenant_norm)
    profile = ledger.load_balances(operator_id)

    deltas = compute_deltas(
        event_type,
        discovery_receipt,
        profile,
        policy=pol,
        governance_status=governance_status,
    )
    if deltas is None:
        return {
            "status": "skipped",
            "summary": f"no reward for {event_type} under current conditions",
        }

    receipt_id = str(discovery_receipt.get("receipt_id") or "").strip()
    event = build_reward_event(
        event_type=event_type,
        operator_id=operator_id,
        tenant_id=tenant_norm,
        subsystem_id=subsystem_id,
        discovery_receipt_id=receipt_id,
        deltas=deltas,
        discovery_receipt=discovery_receipt,
        governance_mission_id=governance_mission_id,
        promotion_organ_id=promotion_organ_id,
    )

    if skip_if_exists and ledger.has_event(event["event_id"]):
        return {
            "status": "idempotent",
            "summary": "reward already issued",
            "event_id": event["event_id"],
            "profile": profile.to_dict(),
        }

    reputation = float(deltas.get("reputation") or 0)
    rail_credits = float(deltas.get("rail_credits") or 0)
    adoption_delta = float(deltas.get("adoption_multiplier") or 0)
    adoption_policy = dict(pol.get("adoption") or {})
    multiplier_cap = float(adoption_policy.get("multiplier_cap") or 3.0)

    preview = {
        "status": "audit",
        "summary": "reward computed (audit-only, no ledger write)",
        "event_id": event["event_id"],
        "event_type": event_type,
        "deltas": event["deltas"],
        "attribution": event.get("attribution"),
        "discovery_receipt_id": receipt_id,
        "economy": {"reputation_primary": True},
        "profile_preview": profile.to_dict(),
    }

    if rewards_audit_only():
        return preview

    if rewards_shadow_only():
        return {
            **preview,
            "status": "shadow",
            "summary": "reward validated (shadow-only, no balance write)",
        }

    profile.apply_deltas(
        reputation=reputation,
        rail_credits=rail_credits,
        adoption_multiplier_delta=adoption_delta,
        subsystem_id=subsystem_id,
        multiplier_cap=multiplier_cap,
        issued_at=float(event["issued_at"]),
    )
    ledger.save_balances(profile)

    reward_receipt = build_operator_reward_receipt(
        event,
        profile.to_dict(),
        runtime_dir=runtime_dir,
    )
    record = {**event, "operator_reward_receipt": reward_receipt}
    ledger.append_event(record)

    return {
        "status": "issued",
        "summary": f"reward issued for {event_type}",
        "event_id": event["event_id"],
        "event_type": event_type,
        "deltas": event["deltas"],
        "attribution": event.get("attribution"),
        "economy": {"reputation_primary": True},
        "operator_reward_receipt": reward_receipt,
        "profile": profile.to_dict(),
    }
