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
        if contribution_type in {"subsystem", "workflow", "organ"} and "standing" not in spec_payload:
            from src.ugr.discovery.standing import Standing, enrich_payload_with_standing

            spec_payload = enrich_payload_with_standing(spec_payload, standing=Standing.ASSERTED)
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
            response["operator_rewards"] = self._emit_rewards(
                existing,
                skip_if_idempotent=True,
            )
            response["library_pattern_rewards"] = self._emit_library_pattern_match_rewards(
                existing
            )
            response["discovery_pod_ledger"] = self._upgrade_pod_ledger(
                operator_id=operator_id,
                tenant_id=tenant_id,
                contribution_id=cid,
                contribution_type=contribution_type,
                spec_payload=spec_payload,
                receipt=existing,
                idempotent_rediscovery=True,
                operator_rewards=response.get("operator_rewards"),
                receipt_verified=ok,
            )
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
        response["library_pattern_rewards"] = self._emit_library_pattern_match_rewards(receipt)
        response["discovery_pod_ledger"] = self._upgrade_pod_ledger(
            operator_id=operator_id,
            tenant_id=tenant_id,
            contribution_id=cid,
            contribution_type=contribution_type,
            spec_payload=spec_payload,
            receipt=receipt,
            idempotent_rediscovery=False,
            operator_rewards=response.get("operator_rewards"),
        )
        return response

    def _upgrade_pod_ledger(
        self,
        *,
        operator_id: str,
        tenant_id: str,
        contribution_id: str,
        contribution_type: str,
        spec_payload: dict[str, Any],
        receipt: dict[str, Any],
        idempotent_rediscovery: bool,
        operator_rewards: dict[str, Any] | None = None,
        receipt_verified: bool | None = None,
    ) -> dict[str, Any]:
        try:
            from src.ugr.discovery.discovery_pod_ledger import attach_discovery_pod_ledger

            ledger_result = attach_discovery_pod_ledger(
                operator_id=operator_id,
                tenant_id=tenant_id,
                contribution_id=contribution_id,
                contribution_type=contribution_type,
                spec_payload=spec_payload,
                receipt=receipt,
                idempotent_rediscovery=idempotent_rediscovery,
                operator_rewards=operator_rewards,
                receipt_verified=receipt_verified,
            )
            return ledger_result
        except Exception as exc:
            return {"ok": False, "errors": [str(exc)]}

    def _emit_rewards(self, receipt: dict[str, Any], *, skip_if_idempotent: bool = False) -> dict[str, Any]:
        try:
            from src.ugr.discovery.library_patterns import rewards_suppressed_for_receipt
            from src.ugr.discovery.proven_contribution import is_proven_contribution
            from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine
            from src.ugr.rewards.operator_reward_spec import event_type_for_contribution

            if rewards_suppressed_for_receipt(receipt):
                return {
                    "status": "suppressed",
                    "summary": "library reference; registration rewards suppressed",
                    "deltas": {},
                }

            proven = is_proven_contribution(receipt)
            if skip_if_idempotent and not proven:
                return {"status": "skipped", "summary": "idempotent discovery"}

            engine = build_operator_reward_engine(self.runtime_dir)
            ctype = str(receipt.get("contribution_type") or ContributionType.SUBSYSTEM.value)
            event_type = event_type_for_contribution(ctype, stage="discovered")
            return engine.issue_contribution(
                receipt=receipt,
                event_type=event_type,
                force_persist=proven,
            )
        except Exception as exc:
            return {"status": "error", "summary": str(exc)}

    def _emit_library_pattern_match_rewards(self, receipt: dict[str, Any]) -> dict[str, Any]:
        """Issue matcher rewards per qualifying contribution (any operator, repeatable).

        Idempotency is keyed by operator_id + contribution_id + pattern_id — not capped
        to a single beneficiary across the library lifetime.
        """
        try:
            from src.ugr.discovery.library_patterns import (
                is_library_reference_contribution,
                match_library_patterns_from_receipt,
            )
            from src.ugr.rewards.operator_reward_spec import EVENT_LIBRARY_PATTERN_MATCHED
            from src.ugr.rewards.reward_issuer import issue_reward

            if is_library_reference_contribution(receipt):
                return {"status": "skipped", "summary": "library reference contribution"}

            matches = match_library_patterns_from_receipt(receipt)
            if not matches:
                return {"status": "skipped", "summary": "no library pattern match"}

            tenant_id = str(receipt.get("tenant_id") or "global")
            operator_id = str(receipt.get("operator_id") or "").strip()
            contribution_id = str(receipt.get("contribution_id") or "")
            if not operator_id or not contribution_id:
                return {"status": "skipped", "summary": "missing operator or contribution id"}

            outcomes: list[dict[str, Any]] = []
            for match in matches:
                pattern_id = str(match.get("pattern_id") or "").strip()
                if not pattern_id:
                    continue
                outcome = issue_reward(
                    tenant_id=tenant_id,
                    operator_id=operator_id,
                    contribution_id=contribution_id,
                    event_type=EVENT_LIBRARY_PATTERN_MATCHED,
                    discovery_receipt=receipt,
                    discovery_receipt_id=str(receipt.get("receipt_id") or ""),
                    primary_anchor=pattern_id,
                    secondary_anchor=contribution_id,
                )
                outcomes.append({"pattern_id": pattern_id, **outcome})
            return {"status": "matched", "matches": outcomes}
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
