"""Organ contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ugr.mission.provider_organ import ProviderOrganRegistry


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)
    organ_id: str = ""


def validate_organ_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    organ_id = str(payload.get("organ_id") or "").strip()
    governance_mission_id = str(payload.get("governance_mission_id") or "").strip()
    if not organ_id:
        result.errors.append("organ_id is required")
        return result
    if not governance_mission_id:
        result.errors.append("governance_mission_id is required")
        return result
    registry = ProviderOrganRegistry(tenant_id=tenant_id)
    organ = registry.get(organ_id)
    if organ is None:
        result.errors.append(f"organ not found: {organ_id}")
        return result
    if str(organ.status or "") != "admitted":
        result.errors.append(f"organ not admitted: {organ.status}")
        return result
    result.organ_id = organ_id
    result.invariants.append({"family": "organ_admit", "status": "pass", "details": organ_id})
    result.proof = {
        "organ_id": organ_id,
        "governance_mission_id": governance_mission_id,
        "provider": organ.provider,
        "law_id": "URG_PROVIDER_ORGAN_CONTRACT",
    }
    result.valid = True
    return result
