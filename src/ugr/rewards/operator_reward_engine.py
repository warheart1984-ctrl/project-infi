"""Operator reward engine — emit anchored incentives for discovery lifecycle."""

from __future__ import annotations

import os
from typing import Any

from src.ugr.discovery.subsystem_discovery_receipt import verify_subsystem_discovery_receipt
from src.ugr.platform.tenant_registry import normalize_tenant_id
from src.ugr.rewards.operator_reward_receipt import build_operator_reward_receipt
from src.ugr.rewards.operator_reward_store import OperatorRewardStore
from src.ugr.rewards.reward_events import (
    EVENT_SUBSYSTEM_ADOPTED,
    EVENT_SUBSYSTEM_DISCOVERED,
    EVENT_SUBSYSTEM_PROMOTED,
    build_reward_event,
)
from src.ugr.rewards.reward_policy import cap_rail_credit_earn, load_reward_policy


UGR_OPERATOR_REWARDS_ENABLED_ENV = "UGR_OPERATOR_REWARDS_ENABLED"


def rewards_enabled() -> bool:
    raw = os.getenv(UGR_OPERATOR_REWARDS_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


class OperatorRewardEngine:
    def __init__(self, runtime_dir: str | None = None, *, policy: dict[str, Any] | None = None):
        self.runtime_dir = runtime_dir
        self.policy = policy or load_reward_policy()

    def _store(self, tenant_id: str) -> OperatorRewardStore:
        return OperatorRewardStore(self.runtime_dir, tenant_id=tenant_id)

    def _emit(
        self,
        *,
        event_type: str,
        operator_id: str,
        tenant_id: str,
        subsystem_id: str,
        discovery_receipt_id: str,
        reputation: float,
        rail_credits: float,
        adoption_multiplier_delta: float = 0,
        governance_mission_id: str | None = None,
        promotion_organ_id: str | None = None,
        skip_if_exists: bool = True,
    ) -> dict[str, Any]:
        if not rewards_enabled():
            return {"status": "disabled", "summary": "operator rewards disabled"}

        tenant_norm = normalize_tenant_id(tenant_id)
        adoption_policy = dict(self.policy.get("adoption") or {})
        multiplier_cap = float(adoption_policy.get("multiplier_cap") or 3.0)

        store = self._store(tenant_norm)
        profile = store.load_profile(operator_id)
        rail_credits = cap_rail_credit_earn(
            reputation,
            rail_credits,
            profile_reputation=profile.reputation_score,
            policy=self.policy,
        )

        event = build_reward_event(
            event_type=event_type,
            operator_id=operator_id,
            tenant_id=tenant_norm,
            subsystem_id=subsystem_id,
            discovery_receipt_id=discovery_receipt_id,
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            deltas={
                "reputation": reputation,
                "rail_credits": rail_credits,
                "adoption_multiplier": adoption_multiplier_delta,
            },
        )

        if skip_if_exists and store.has_event(event["event_id"], operator_id):
            return {
                "status": "idempotent",
                "summary": "reward already issued",
                "event_id": event["event_id"],
                "profile": profile.to_dict(),
            }

        profile.apply_deltas(
            reputation=reputation,
            rail_credits=rail_credits,
            adoption_multiplier_delta=adoption_multiplier_delta,
            subsystem_id=subsystem_id,
            multiplier_cap=multiplier_cap,
            issued_at=float(event["issued_at"]),
        )
        store.save_profile(profile)

        receipt = build_operator_reward_receipt(
            event,
            profile.to_dict(),
            runtime_dir=self.runtime_dir,
        )
        record = {**event, "operator_reward_receipt": receipt}
        store.append_reward(record, operator_id=operator_id)

        return {
            "status": "issued",
            "summary": f"reward issued for {event_type}",
            "event_id": event["event_id"],
            "event_type": event_type,
            "deltas": event["deltas"],
            "attribution": event.get("attribution"),
            "economy": {"reputation_primary": True},
            "operator_reward_receipt": receipt,
            "profile": profile.to_dict(),
        }

    def emit_for_discovery(
        self,
        discovery_receipt: dict[str, Any],
        *,
        skip_if_idempotent: bool = False,
    ) -> dict[str, Any]:
        if not rewards_enabled():
            return {"status": "disabled", "summary": "operator rewards disabled"}
        if skip_if_idempotent:
            return {
                "status": "skipped",
                "summary": "idempotent discovery — no new rewards",
            }

        ok, reason = verify_subsystem_discovery_receipt(
            discovery_receipt,
            runtime_dir=self.runtime_dir,
        )
        if not ok:
            return {"status": "rejected", "summary": f"discovery receipt invalid: {reason}"}

        disc_policy = dict(self.policy.get("discovery") or {})
        reputation = float(disc_policy.get("reputation") or 0)
        rail_credits = float(disc_policy.get("rail_credits") or 0)

        search_bonus = dict(disc_policy.get("search_efficiency_bonus") or {})
        if str(discovery_receipt.get("discovery_mode") or "") == "search":
            max_attempts = int(search_bonus.get("max_attempts") or 8)
            if int(discovery_receipt.get("search_attempts") or 0) <= max_attempts:
                reputation += float(search_bonus.get("reputation") or 0)
                rail_credits += float(search_bonus.get("rail_credits") or 0)

        return self._emit(
            event_type=EVENT_SUBSYSTEM_DISCOVERED,
            operator_id=str(discovery_receipt.get("operator_id") or ""),
            tenant_id=str(discovery_receipt.get("tenant_id") or ""),
            subsystem_id=str(discovery_receipt.get("subsystem_id") or ""),
            discovery_receipt_id=str(discovery_receipt.get("receipt_id") or ""),
            reputation=reputation,
            rail_credits=rail_credits,
        )

    def emit_for_promotion(
        self,
        discovery_receipt: dict[str, Any],
        *,
        governance_mission_id: str,
        promotion_organ_id: str,
        governance_status: str,
    ) -> dict[str, Any]:
        if str(governance_status or "").lower() not in {"ok", "completed"}:
            return {
                "status": "skipped",
                "summary": f"promotion not successful: {governance_status}",
            }

        promo_policy = dict(self.policy.get("promotion") or {})
        return self._emit(
            event_type=EVENT_SUBSYSTEM_PROMOTED,
            operator_id=str(discovery_receipt.get("operator_id") or ""),
            tenant_id=str(discovery_receipt.get("tenant_id") or ""),
            subsystem_id=str(discovery_receipt.get("subsystem_id") or ""),
            discovery_receipt_id=str(discovery_receipt.get("receipt_id") or ""),
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            reputation=float(promo_policy.get("reputation") or 0),
            rail_credits=float(promo_policy.get("rail_credits") or 0),
        )

    def emit_for_adoption(
        self,
        *,
        operator_id: str,
        tenant_id: str,
        subsystem_id: str,
        discovery_receipt_id: str,
        promotion_organ_id: str,
    ) -> dict[str, Any]:
        adopt_policy = dict(self.policy.get("adoption") or {})
        store = self._store(tenant_id)
        profile = store.load_profile(operator_id)
        multiplier = float(profile.adoption_multipliers.get(subsystem_id) or 1.0)
        base_rep = float(adopt_policy.get("reputation") or 0)
        if adopt_policy.get("reputation_scales_with_multiplier", True):
            base_rep = base_rep * multiplier
        return self._emit(
            event_type=EVENT_SUBSYSTEM_ADOPTED,
            operator_id=operator_id,
            tenant_id=tenant_id,
            subsystem_id=subsystem_id,
            discovery_receipt_id=discovery_receipt_id,
            promotion_organ_id=promotion_organ_id,
            reputation=base_rep,
            rail_credits=float(adopt_policy.get("rail_credits") or 0),
            adoption_multiplier_delta=float(adopt_policy.get("multiplier_increment") or 0),
        )

    def get_profile(self, operator_id: str, *, tenant_id: str) -> dict[str, Any]:
        store = self._store(tenant_id)
        return store.load_profile(operator_id).to_dict()

    def list_ledger(
        self,
        *,
        tenant_id: str,
        operator_id: str | None = None,
        subsystem_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        store = self._store(tenant_id)
        return store.list_events(
            operator_id=operator_id,
            subsystem_id=subsystem_id,
            limit=limit,
        )


def build_operator_reward_engine(runtime_dir: str | None = None) -> OperatorRewardEngine:
    return OperatorRewardEngine(runtime_dir=runtime_dir)


def try_emit_adoption_from_mission(
    *,
    tenant_id: str,
    mission_id: str,
    steps: list[dict[str, Any]],
    status: str,
    runtime_dir: str | None = None,
    organ_registry: Any | None = None,
) -> list[dict[str, Any]]:
    """Scan completed mission steps for discovered organ usage and emit adoption rewards."""
    if status != "ok" or not rewards_enabled():
        return []

    from src.ugr.discovery.subsystem_discovery_store import SubsystemDiscoveryStore
    from src.ugr.mission.provider_organ import ProviderOrganRegistry

    results: list[dict[str, Any]] = []
    registry = organ_registry or ProviderOrganRegistry(tenant_id=tenant_id)
    engine = OperatorRewardEngine(runtime_dir=runtime_dir)
    catalog = SubsystemDiscoveryStore(runtime_dir=runtime_dir, tenant_id=tenant_id).list_catalog(limit=500)

    receipt_by_id = {
        str(entry.get("receipt_id") or ""): entry
        for entry in catalog
        if entry.get("receipt_id")
    }

    seen_organs: set[str] = set()
    for step in steps:
        if str(step.get("status") or "") != "ok":
            continue
        organ_id = str(step.get("organ_id") or "").strip()
        if not organ_id or not organ_id.startswith("discovered-") or organ_id in seen_organs:
            continue
        seen_organs.add(organ_id)
        organ = registry.get(organ_id)
        if organ is None:
            continue
        admission_id = str(organ.admission_receipt_id or "").strip()
        if not admission_id:
            continue
        catalog_entry = receipt_by_id.get(admission_id) or {}
        operator_id = str(catalog_entry.get("operator_id") or "").strip()
        if not operator_id:
            continue
        discovery_store = SubsystemDiscoveryStore(runtime_dir=runtime_dir, tenant_id=tenant_id)
        receipt = discovery_store.get_by_subsystem_id(str(catalog_entry.get("subsystem_id") or ""))
        if not receipt:
            continue
        result = engine.emit_for_adoption(
            operator_id=operator_id,
            tenant_id=tenant_id,
            subsystem_id=str(receipt.get("subsystem_id") or ""),
            discovery_receipt_id=admission_id,
            promotion_organ_id=organ_id,
        )
        result["mission_id"] = mission_id
        results.append(result)
    return results
