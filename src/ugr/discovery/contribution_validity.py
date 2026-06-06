"""Dispatch contribution validity checks by type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ugr.discovery.contribution_spec import ContributionSpec, ContributionType, validate_contribution_shape
from src.ugr.discovery.validators.capability import validate_capability_contribution
from src.ugr.discovery.validators.invariant import validate_invariant_contribution
from src.ugr.discovery.validators.organ import validate_organ_contribution
from src.ugr.discovery.validators.proof_packet import validate_proof_contribution
from src.ugr.discovery.validators.substrate import validate_substrate_contribution
from src.ugr.discovery.validators.subsystem import validate_subsystem_contribution
from src.ugr.discovery.validators.workflow import validate_workflow_contribution


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)
    organs_matched: list[dict[str, str]] = field(default_factory=list)
    rail_proof: dict[str, Any] = field(default_factory=dict)
    genome_metadata: dict[str, Any] = field(default_factory=dict)
    organ_id: str = ""


def _normalize_result(raw: Any) -> ValidityResult:
    if isinstance(raw, ValidityResult):
        return raw
    proof = dict(getattr(raw, "proof", None) or getattr(raw, "rail_proof", None) or {})
    return ValidityResult(
        valid=bool(getattr(raw, "valid", False)),
        errors=list(getattr(raw, "errors", None) or []),
        invariants=list(getattr(raw, "invariants", None) or []),
        proof=proof,
        organs_matched=list(getattr(raw, "organs_matched", None) or []),
        rail_proof=dict(getattr(raw, "rail_proof", None) or proof),
        genome_metadata=dict(getattr(raw, "genome_metadata", None) or {}),
        organ_id=str(getattr(raw, "organ_id", None) or ""),
    )


def validate_contribution_spec(
    spec: ContributionSpec,
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    shape_errors = validate_contribution_shape(spec)
    if shape_errors:
        return ValidityResult(valid=False, errors=shape_errors)

    ctype = spec.contribution_type
    common = {
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "aais_instance_id": aais_instance_id,
        "constraints": constraints,
    }

    if ctype == ContributionType.SUBSYSTEM.value:
        return _normalize_result(validate_subsystem_contribution(spec, **common))
    if ctype == ContributionType.WORKFLOW.value:
        return _normalize_result(validate_workflow_contribution(spec.payload, **common))
    if ctype == ContributionType.ORGAN.value:
        return _normalize_result(validate_organ_contribution(spec.payload, **common))
    if ctype == ContributionType.PROOF.value:
        return _normalize_result(validate_proof_contribution(spec.payload, **common))
    if ctype == ContributionType.INVARIANT.value:
        return _normalize_result(validate_invariant_contribution(spec.payload, **common))
    if ctype == ContributionType.CAPABILITY.value:
        return _normalize_result(validate_capability_contribution(spec.payload, **common))
    if ctype == ContributionType.SUBSTRATE.value:
        return _normalize_result(validate_substrate_contribution(spec.payload, **common))

    return ValidityResult(valid=False, errors=[f"unsupported contribution_type: {ctype}"])
