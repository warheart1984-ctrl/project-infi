"""Subsystem contribution validator — delegates to Proof-of-Subsystem."""

from __future__ import annotations

from typing import Any

from src.ugr.discovery.contribution_spec import ContributionSpec
from src.ugr.discovery.subsystem_spec import SubsystemSpec
from src.ugr.discovery.subsystem_validity import ValidityResult, validate_subsystem_spec


def validate_subsystem_contribution(
    spec: ContributionSpec,
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    subsystem = SubsystemSpec.from_dict(spec.payload)
    return validate_subsystem_spec(
        subsystem,
        tenant_id=tenant_id,
        operator_id=operator_id,
        aais_instance_id=aais_instance_id,
        constraints=constraints,
    )
