"""Subsystem discovery orchestrator — validate, search, receipt, promote."""

from __future__ import annotations

import os
from itertools import product
from typing import Any
from uuid import uuid4

from src.ugr.discovery.subsystem_discovery_receipt import (
    build_subsystem_discovery_receipt,
    verify_subsystem_discovery_receipt,
)
from src.ugr.discovery.subsystem_discovery_store import SubsystemDiscoveryStore
from src.ugr.discovery.subsystem_spec import (
    RAIL_CLASSES,
    RISK_CEILINGS,
    SubsystemSpec,
    subsystem_id_from_spec,
)
from src.ugr.discovery.subsystem_validity import ValidityResult, validate_subsystem_spec
from src.ugr.platform.tenant_registry import normalize_tenant_id


UGR_SUBSYSTEM_DISCOVERY_ENABLED_ENV = "UGR_SUBSYSTEM_DISCOVERY_ENABLED"
UGR_DISCOVERY_SHADOW_ONLY_ENV = "UGR_DISCOVERY_SHADOW_ONLY"
URG_GOVERNANCE_APPLY_ENV = "URG_GOVERNANCE_APPLY"

DEFAULT_MAX_ATTEMPTS = 64
MAX_ATTEMPTS_CAP = 256


def discovery_enabled() -> bool:
    raw = os.getenv(UGR_SUBSYSTEM_DISCOVERY_ENABLED_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def shadow_only_default() -> bool:
    raw = os.getenv(UGR_DISCOVERY_SHADOW_ONLY_ENV, "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def governance_apply_enabled() -> bool:
    raw = os.getenv(URG_GOVERNANCE_APPLY_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _is_complete_spec(spec: SubsystemSpec) -> bool:
    return spec.is_complete()


def _enumerate_candidates(
    seed: SubsystemSpec,
    constraints: dict[str, Any],
    *,
    max_attempts: int,
) -> list[SubsystemSpec]:
    roles = list(constraints.get("roles") or [])
    if not roles and seed.role:
        roles = [seed.role]
    if not roles:
        roles = ["llm_executor"]

    rails = [str(r).upper() for r in (constraints.get("rail_classes") or []) if str(r).upper() in RAIL_CLASSES]
    if not rails:
        rails = [seed.rail_class] if seed.rail_class in RAIL_CLASSES else ["SAFE", "NORMAL", "EXPRESS"]

    risks = [str(r).lower() for r in (constraints.get("risk_ceilings") or []) if str(r).lower() in RISK_CEILINGS]
    if not risks:
        risks = ["low", "medium", "high"]

    tenant_classes = [str(t).lower() for t in (constraints.get("tenant_classes") or [])]
    if not tenant_classes:
        tenant_classes = [seed.tenant_class or "standard"]

    io_inputs = list((constraints.get("io_inputs") or seed.io_shape.get("inputs") or ["text"]))
    io_outputs = list((constraints.get("io_outputs") or seed.io_shape.get("outputs") or ["text"]))

    candidates: list[SubsystemSpec] = []
    for role, rail, risk, tclass in product(roles, rails, risks, tenant_classes):
        spec = SubsystemSpec.from_dict(
            {
                "role": role,
                "rail_class": rail,
                "risk_ceiling": risk,
                "tenant_class": tclass,
                "io_shape": {"inputs": io_inputs, "outputs": io_outputs},
            }
        )
        candidates.append(spec)
        if len(candidates) >= max_attempts:
            break
    return candidates


class SubsystemDiscoveryService:
    def __init__(self, runtime_dir: str | None = None):
        self.runtime_dir = runtime_dir

    def _store(self, tenant_id: str) -> SubsystemDiscoveryStore:
        return SubsystemDiscoveryStore(self.runtime_dir, tenant_id=tenant_id)

    def discover(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if not discovery_enabled():
            return {"status": "rejected", "summary": "subsystem discovery disabled"}

        tenant_id = normalize_tenant_id(payload.get("tenant_id"))
        operator_id = str(payload.get("operator_id") or "").strip()
        aais_instance_id = str(payload.get("aais_instance_id") or "").strip()
        if not operator_id or not aais_instance_id:
            return {"status": "rejected", "summary": "operator_id and aais_instance_id required"}

        constraints = dict(payload.get("constraints") or {})
        seed_raw = dict(payload.get("seed") or {})
        spec_raw = dict(payload.get("spec") or {})
        merged_seed = SubsystemSpec.from_dict({**seed_raw, **spec_raw})

        max_attempts = int(payload.get("max_attempts") or 0)
        if max_attempts <= 0 and not _is_complete_spec(merged_seed):
            max_attempts = DEFAULT_MAX_ATTEMPTS
        max_attempts = min(max_attempts, MAX_ATTEMPTS_CAP)

        promote = bool(payload.get("promote"))
        search_trail: list[dict[str, Any]] = []

        if _is_complete_spec(merged_seed) and max_attempts == 0:
            return self._finalize_discovery(
                merged_seed,
                tenant_id=tenant_id,
                operator_id=operator_id,
                aais_instance_id=aais_instance_id,
                constraints=constraints,
                discovery_mode="validate",
                search_attempts=0,
                search_trail=search_trail,
                promote=promote,
            )

        candidates = [merged_seed] if _is_complete_spec(merged_seed) else []
        if not candidates:
            candidates = _enumerate_candidates(merged_seed, constraints, max_attempts=max_attempts or DEFAULT_MAX_ATTEMPTS)

        attempts = 0
        for candidate in candidates:
            attempts += 1
            validity = validate_subsystem_spec(
                candidate,
                tenant_id=tenant_id,
                operator_id=operator_id,
                aais_instance_id=aais_instance_id,
                constraints=constraints,
            )
            search_trail.append(
                {
                    "attempt": attempts,
                    "subsystem_id": subsystem_id_from_spec(candidate),
                    "valid": validity.valid,
                    "errors": list(validity.errors)[:3],
                }
            )
            if validity.valid:
                return self._finalize_discovery(
                    candidate,
                    tenant_id=tenant_id,
                    operator_id=operator_id,
                    aais_instance_id=aais_instance_id,
                    constraints=constraints,
                    discovery_mode="search",
                    search_attempts=attempts,
                    search_trail=search_trail,
                    promote=promote,
                    validity=validity,
                )

        return {
            "status": "not_found",
            "summary": "no valid subsystem spec found within search envelope",
            "search_attempts": attempts,
            "search_trail": search_trail[-8:],
        }

    def _finalize_discovery(
        self,
        spec: SubsystemSpec,
        *,
        tenant_id: str,
        operator_id: str,
        aais_instance_id: str,
        constraints: dict[str, Any],
        discovery_mode: str,
        search_attempts: int,
        search_trail: list[dict[str, Any]],
        promote: bool,
        validity: ValidityResult | None = None,
    ) -> dict[str, Any]:
        validity = validity or validate_subsystem_spec(
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
                "subsystem_id": subsystem_id_from_spec(spec),
                "invariants": validity.invariants,
                "errors": validity.errors,
            }

        store = self._store(tenant_id)
        sid = subsystem_id_from_spec(spec)
        existing = store.get_by_subsystem_id(sid)
        if existing:
            ok, reason = verify_subsystem_discovery_receipt(existing, runtime_dir=self.runtime_dir)
            response = {
                "status": "discovered",
                "summary": "already discovered",
                "subsystem_id": sid,
                "subsystem_discovery_receipt": existing,
                "receipt_verified": ok,
                "receipt_verify_reason": reason,
                "idempotent": True,
            }
            response["operator_rewards"] = self._emit_discovery_rewards(
                existing,
                skip_if_idempotent=True,
            )
            return response

        receipt = build_subsystem_discovery_receipt(
            spec,
            validity,
            tenant_id=tenant_id,
            operator_id=operator_id,
            aais_instance_id=aais_instance_id,
            discovery_mode=discovery_mode,
            search_attempts=search_attempts,
            search_trail=search_trail,
            runtime_dir=self.runtime_dir,
        )
        store.persist_discovery(receipt, tenant_id=tenant_id)
        store.append_catalog(receipt, tenant_id=tenant_id)

        response: dict[str, Any] = {
            "status": "discovered",
            "summary": "subsystem spec passed invariants",
            "subsystem_id": sid,
            "subsystem_discovery_receipt": receipt,
            "catalog_status": "shadow",
        }
        response["operator_rewards"] = self._emit_discovery_rewards(receipt)

        if promote:
            response["promotion"] = self._attempt_promotion(
                receipt,
                spec=spec,
                validity=validity,
                tenant_id=tenant_id,
                operator_id=operator_id,
                aais_instance_id=aais_instance_id,
            )
        return response

    def _attempt_promotion(
        self,
        receipt: dict[str, Any],
        *,
        spec: SubsystemSpec,
        validity: ValidityResult,
        tenant_id: str,
        operator_id: str,
        aais_instance_id: str,
    ) -> dict[str, Any]:
        if shadow_only_default() and not governance_apply_enabled():
            return {
                "status": "blocked",
                "summary": "promotion requires URG_GOVERNANCE_APPLY=1 and UGR_DISCOVERY_SHADOW_ONLY=0",
            }
        if not governance_apply_enabled():
            return {
                "status": "blocked",
                "summary": "promotion requires URG_GOVERNANCE_APPLY=1",
            }

        template_id = validity.organ_id or (
            validity.organs_matched[0].get("organ_id") if validity.organs_matched else ""
        )
        from src.ugr.mission.provider_organ import ProviderOrganRegistry

        registry = ProviderOrganRegistry(tenant_id=tenant_id)
        template = registry.get(template_id) if template_id else None
        if template is None:
            return {"status": "blocked", "summary": f"template organ not found: {template_id}"}

        draft_id = f"discovered-{spec.role}-{str(uuid4())[:8]}"
        organ_spec = template.to_dict()
        organ_spec["organ_id"] = draft_id
        organ_spec["tenant_scope"] = tenant_id
        organ_spec["status"] = "admitted"
        organ_spec["admission_receipt_id"] = receipt.get("receipt_id")
        identity = dict(organ_spec.get("identity") or {})
        identity["organ_id"] = draft_id
        identity["label"] = f"Discovered {spec.role}"
        organ_spec["identity"] = identity
        mutation_payload = {
            "mission_kind": "governance_mutation",
            "mutation_target": "provider_organs",
            "mutation_op": "organ_admit",
            "operator_id": operator_id,
            "aais_instance_id": aais_instance_id,
            "tenant_id": tenant_id,
            "governance_authority": "subsystem_discovery",
            "discovery_subsystem_id": receipt.get("subsystem_id"),
            "organ_id": draft_id,
            "organ_spec": organ_spec,
        }
        from src.ugr.mission.governance_mission import run_governance_mission
        from src.ugr.mission.mission_runtime import UGRMissionRuntime

        runtime = UGRMissionRuntime(runtime_dir=self.runtime_dir)
        result = run_governance_mission(mutation_payload, runtime=runtime)
        promotion_response = {
            "status": str(result.get("status") or "unknown"),
            "summary": str(result.get("summary") or ""),
            "governance_result": result,
        }
        promotion_response["operator_rewards"] = self._emit_promotion_rewards(
            receipt,
            governance_result=result,
            promotion_organ_id=draft_id,
        )
        return promotion_response

    def _emit_discovery_rewards(
        self,
        receipt: dict[str, Any],
        *,
        skip_if_idempotent: bool = False,
    ) -> dict[str, Any]:
        try:
            from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine

            return build_operator_reward_engine(self.runtime_dir).emit_for_discovery(
                receipt,
                skip_if_idempotent=skip_if_idempotent,
            )
        except Exception as exc:
            return {"status": "error", "summary": str(exc)}

    def _emit_promotion_rewards(
        self,
        receipt: dict[str, Any],
        *,
        governance_result: dict[str, Any],
        promotion_organ_id: str,
    ) -> dict[str, Any]:
        try:
            from src.ugr.rewards.operator_reward_engine import build_operator_reward_engine

            mission_id = str(
                governance_result.get("mission_id")
                or (governance_result.get("urg_ingress") or {}).get("mission_id")
                or ""
            )
            return build_operator_reward_engine(self.runtime_dir).emit_for_promotion(
                receipt,
                governance_mission_id=mission_id,
                promotion_organ_id=promotion_organ_id,
                governance_status=str(governance_result.get("status") or ""),
            )
        except Exception as exc:
            return {"status": "error", "summary": str(exc)}

    def get_receipt(self, subsystem_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        return self._store(tenant_id).get_by_subsystem_id(subsystem_id)

    def list_discoveries(
        self,
        *,
        tenant_id: str,
        since: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return self._store(tenant_id).list_catalog(since=since, limit=limit)


def build_subsystem_discovery_service(runtime_dir: str | None = None) -> SubsystemDiscoveryService:
    return SubsystemDiscoveryService(runtime_dir=runtime_dir)
