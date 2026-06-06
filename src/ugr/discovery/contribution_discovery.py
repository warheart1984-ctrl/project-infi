"""Unified contribution discovery orchestrator."""

# Mythic: Contribution Discovery
# Engineering: ContributionDiscoveryEngine
from __future__ import annotations

import os
from typing import Any

from src.ugr.discovery.contribution_discovery_receipt import (
    build_contribution_discovery_receipt,
    verify_contribution_discovery_receipt,
)
from src.ugr.discovery.contribution_spec import ContributionSpec, ContributionType
from src.ugr.discovery.contribution_store import ContributionDiscoveryStore
from src.ugr.discovery.contribution_validity import validate_contribution_spec
from src.ugr.discovery.subsystem_discovery import (
    SubsystemDiscoveryService,
    build_subsystem_discovery_service,
    discovery_enabled,
    governance_apply_enabled,
    shadow_only_default,
)
from src.ugr.discovery.subsystem_spec import SubsystemSpec
from src.ugr.platform.tenant_registry import normalize_tenant_id


UGR_CONTRIBUTION_DISCOVERY_ENABLED_ENV = "UGR_SUBSYSTEM_DISCOVERY_ENABLED"


class ContributionDiscoveryService:
    def __init__(self, runtime_dir: str | None = None):
        self.runtime_dir = runtime_dir
        self._subsystem = SubsystemDiscoveryService(runtime_dir)

    def _store(self, tenant_id: str) -> ContributionDiscoveryStore:
        return ContributionDiscoveryStore(self.runtime_dir, tenant_id=tenant_id)

    def discover(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not discovery_enabled():
            return {"status": "rejected", "summary": "contribution discovery disabled"}

        contribution_type = str(
            payload.get("contribution_type") or payload.get("type") or ContributionType.SUBSYSTEM.value
        ).strip().lower()

        if contribution_type == ContributionType.SUBSYSTEM.value and payload.get("spec"):
            return self._subsystem.discover(payload)

        tenant_id = normalize_tenant_id(payload.get("tenant_id"))
        operator_id = str(payload.get("operator_id") or "").strip()
        aais_instance_id = str(payload.get("aais_instance_id") or "").strip()
        if not operator_id or not aais_instance_id:
            return {"status": "rejected", "summary": "operator_id and aais_instance_id required"}

        spec_payload = dict(payload.get("payload") or payload.get("spec") or {})
        spec = ContributionSpec(contribution_type=contribution_type, payload=spec_payload)
        constraints = dict(payload.get("constraints") or {})

        validity = validate_contribution_spec(
            spec,
            tenant_id=tenant_id,
            operator_id=operator_id,
            aais_instance_id=aais_instance_id,
            constraints=constraints,
        )
        if not validity.valid:
            return {
                "status": "invalid",
                "summary": "; ".join(validity.errors) or "validation failed",
                "contribution_id": spec.contribution_id(),
                "contribution_type": contribution_type,
                "errors": validity.errors,
                "invariants": validity.invariants,
            }

        store = self._store(tenant_id)
        cid = spec.contribution_id()
        existing = store.get_by_contribution_id(cid)
        if existing:
            ok, reason = verify_contribution_discovery_receipt(existing, runtime_dir=self.runtime_dir)
            response = {
                "status": "discovered",
                "summary": "already discovered",
                "contribution_id": cid,
                "contribution_type": contribution_type,
                "contribution_discovery_receipt": existing,
                "receipt_verified": ok,
                "receipt_verify_reason": reason,
                "idempotent": True,
            }
            if contribution_type == ContributionType.SUBSYSTEM.value:
                response["subsystem_id"] = cid
                response["subsystem_discovery_receipt"] = existing
            response["operator_rewards"] = self._emit_rewards(existing, skip_if_idempotent=True)
            return response

        receipt = build_contribution_discovery_receipt(
            spec,
            validity,
            tenant_id=tenant_id,
            operator_id=operator_id,
            aais_instance_id=aais_instance_id,
            discovery_mode="validate",
            runtime_dir=self.runtime_dir,
        )
        store.persist_discovery(receipt, tenant_id=tenant_id)
        store.append_catalog(receipt, tenant_id=tenant_id)

        response: dict[str, Any] = {
            "status": "discovered",
            "summary": f"{contribution_type} contribution passed validation",
            "contribution_id": cid,
            "contribution_type": contribution_type,
            "contribution_discovery_receipt": receipt,
            "catalog_status": "shadow",
        }
        if contribution_type == ContributionType.SUBSYSTEM.value:
            response["subsystem_id"] = cid
            response["subsystem_discovery_receipt"] = receipt
        response["operator_rewards"] = self._emit_rewards(receipt)
        return response

    def _emit_rewards(self, receipt: dict[str, Any], *, skip_if_idempotent: bool = False) -> dict[str, Any]:
        try:
            from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
            from src.ugr.rewards.operator_reward_spec import event_type_for_contribution

            engine = build_operator_reward_engine(self.runtime_dir)
            ctype = str(receipt.get("contribution_type") or ContributionType.SUBSYSTEM.value)
            event_type = event_type_for_contribution(ctype, stage="discovered")
            if skip_if_idempotent:
                return {"status": "skipped", "summary": "idempotent discovery"}
            return engine.issue_contribution(
                receipt=receipt,
                event_type=event_type,
            )
        except Exception as exc:
            return {"status": "error", "summary": str(exc)}

    def get_receipt(self, contribution_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        return self._store(tenant_id).get_by_contribution_id(contribution_id)

    def list_discoveries(
        self,
        *,
        tenant_id: str,
        contribution_type: str | None = None,
        since: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._store(tenant_id).list_catalog(
            contribution_type=contribution_type,
            since=since,
            limit=limit,
        )


def build_contribution_discovery_service(runtime_dir: str | None = None) -> ContributionDiscoveryService:
    return ContributionDiscoveryService(runtime_dir=runtime_dir)


def discover_subsystem_payload_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Helper: wrap subsystem spec dict as contribution payload."""
    return {
        "contribution_type": ContributionType.SUBSYSTEM.value,
        "payload": SubsystemSpec.from_dict(spec).canonical_dict(),
    }
