"""Operator reward engine — contribution-aware reward issuance."""

from __future__ import annotations

from typing import Any

from src.ugr.discovery.contribution_discovery import ContributionDiscoveryService
from src.ugr.discovery.contribution_spec import ContributionSpec, ContributionType
from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
from src.ugr.rewards.operator_reward_spec import (
    EVENT_SUBSYSTEM_ADOPTED,
    EVENT_SUBSYSTEM_DISCOVERED,
    EVENT_SUBSYSTEM_PROMOTED,
    event_type_for_contribution,
)
from src.ugr.rewards.reward_issuer import (
    UGR_OPERATOR_REWARDS_ENABLED_ENV,
    issue_reward,
    rewards_enabled,
)
from src.ugr.rewards.reward_ledger import RewardLedger
from src.ugr.rewards.reward_policy import load_reward_policy


class OperatorRewardEngine:
    def __init__(self, runtime_dir: str | None = None, *, policy: dict[str, Any] | None = None):
        self.runtime_dir = runtime_dir
        self.policy = policy or load_reward_policy()

    def _ledger(self, tenant_id: str) -> RewardLedger:
        return RewardLedger(self.runtime_dir, tenant_id=tenant_id)

    def maybe_issue(
        self,
        *,
        tenant_id: str,
        operator_id: str,
        contribution_type: str,
        payload: dict[str, Any],
        event_type: str | None = None,
        aais_instance_id: str = "aais-local",
        governance_mission_id: str | None = None,
        promotion_organ_id: str | None = None,
        governance_status: str | None = None,
        auto_discover: bool = True,
    ) -> dict[str, Any]:
        """Discover contribution if needed, then issue reward."""
        if not rewards_enabled():
            return {"status": "disabled", "summary": "operator rewards disabled"}

        evt = event_type or event_type_for_contribution(contribution_type, stage="discovered")
        if auto_discover:
            discovery = ContributionDiscoveryService(self.runtime_dir).discover(
                {
                    "tenant_id": tenant_id,
                    "operator_id": operator_id,
                    "aais_instance_id": aais_instance_id,
                    "contribution_type": contribution_type,
                    "payload": payload,
                }
            )
            if discovery.get("status") not in {"discovered"}:
                return discovery
            receipt = dict(
                discovery.get("contribution_discovery_receipt")
                or discovery.get("subsystem_discovery_receipt")
                or {}
            )
            cid = str(receipt.get("contribution_id") or receipt.get("subsystem_id") or "")
            return self.issue_contribution(
                receipt=receipt,
                event_type=evt,
                governance_mission_id=governance_mission_id,
                promotion_organ_id=promotion_organ_id,
                governance_status=governance_status,
            )

        spec = ContributionSpec(contribution_type=contribution_type, payload=payload)
        return issue_reward(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_id=spec.contribution_id(),
            event_type=evt,
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            governance_status=governance_status,
            runtime_dir=self.runtime_dir,
            policy=self.policy,
        )

    def issue_contribution(
        self,
        *,
        receipt: dict[str, Any],
        event_type: str,
        governance_mission_id: str | None = None,
        promotion_organ_id: str | None = None,
        governance_status: str | None = None,
        skip_if_exists: bool = True,
    ) -> dict[str, Any]:
        cid = str(receipt.get("contribution_id") or receipt.get("subsystem_id") or "")
        return issue_reward(
            tenant_id=str(receipt.get("tenant_id") or ""),
            operator_id=str(receipt.get("operator_id") or ""),
            contribution_id=cid,
            event_type=event_type,
            discovery_receipt_id=str(receipt.get("receipt_id") or ""),
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            governance_status=governance_status,
            runtime_dir=self.runtime_dir,
            policy=self.policy,
            skip_if_exists=skip_if_exists,
        )

    def emit_for_discovery(
        self,
        discovery_receipt: dict[str, Any],
        *,
        skip_if_idempotent: bool = False,
    ) -> dict[str, Any]:
        if not rewards_enabled():
            return {"status": "disabled", "summary": "operator rewards disabled"}
        if skip_if_idempotent:
            return {"status": "skipped", "summary": "idempotent discovery — no new rewards"}
        ctype = str(discovery_receipt.get("contribution_type") or ContributionType.SUBSYSTEM.value)
        evt = event_type_for_contribution(ctype, stage="discovered")
        return self.issue_contribution(receipt=discovery_receipt, event_type=evt)

    def emit_for_promotion(
        self,
        discovery_receipt: dict[str, Any],
        *,
        governance_mission_id: str,
        promotion_organ_id: str,
        governance_status: str,
    ) -> dict[str, Any]:
        return self.issue_contribution(
            receipt=discovery_receipt,
            event_type=EVENT_SUBSYSTEM_PROMOTED,
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            governance_status=governance_status,
        )

    def emit_for_adoption(
        self,
        *,
        operator_id: str,
        tenant_id: str,
        contribution_id: str,
        discovery_receipt_id: str,
        promotion_organ_id: str,
        subsystem_id: str | None = None,
    ) -> dict[str, Any]:
        cid = contribution_id or subsystem_id or ""
        return issue_reward(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_id=cid,
            event_type=EVENT_SUBSYSTEM_ADOPTED,
            discovery_receipt_id=discovery_receipt_id,
            promotion_organ_id=promotion_organ_id,
            runtime_dir=self.runtime_dir,
            policy=self.policy,
        )

    def issue(
        self,
        *,
        tenant_id: str,
        operator_id: str,
        contribution_id: str | None = None,
        subsystem_id: str | None = None,
        event_type: str,
        discovery_receipt_id: str | None = None,
        governance_mission_id: str | None = None,
        promotion_organ_id: str | None = None,
        governance_status: str | None = None,
    ) -> dict[str, Any]:
        return issue_reward(
            tenant_id=tenant_id,
            operator_id=operator_id,
            contribution_id=contribution_id or subsystem_id,
            event_type=event_type,
            discovery_receipt_id=discovery_receipt_id,
            governance_mission_id=governance_mission_id,
            promotion_organ_id=promotion_organ_id,
            governance_status=governance_status,
            runtime_dir=self.runtime_dir,
            policy=self.policy,
        )

    def get_profile(self, operator_id: str, *, tenant_id: str) -> dict[str, Any]:
        return self._ledger(tenant_id).load_balances(operator_id).to_dict()

    def list_ledger(
        self,
        *,
        tenant_id: str,
        operator_id: str | None = None,
        contribution_id: str | None = None,
        subsystem_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._ledger(tenant_id).list_events(
            operator_id=operator_id,
            contribution_id=contribution_id or subsystem_id,
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

    from src.ugr.mission.provider_organ import ProviderOrganRegistry

    results: list[dict[str, Any]] = []
    registry = organ_registry or ProviderOrganRegistry(tenant_id=tenant_id)
    engine = OperatorRewardEngine(runtime_dir=runtime_dir)
    catalog = ContributionDiscoveryStore(runtime_dir=runtime_dir, tenant_id=tenant_id).list_catalog(limit=500)

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
        contribution_id = str(
            catalog_entry.get("contribution_id") or catalog_entry.get("subsystem_id") or ""
        )
        if not contribution_id:
            continue
        result = engine.emit_for_adoption(
            operator_id=operator_id,
            tenant_id=tenant_id,
            contribution_id=contribution_id,
            discovery_receipt_id=admission_id,
            promotion_organ_id=organ_id,
        )
        result["mission_id"] = mission_id
        results.append(result)
    return results
