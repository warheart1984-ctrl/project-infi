"""Substrate / pattern ledger contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)


def validate_substrate_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    claim_id = str(payload.get("claim_id") or "").strip()
    substrate_id = str(payload.get("substrate_id") or "aais.ul_substrate").strip()
    surface = str(payload.get("surface") or "").strip()
    if not claim_id and not surface:
        result.errors.append("claim_id or surface is required")
        return result
    if claim_id and not str(payload.get("classification") or payload.get("status") or "").strip():
        result.errors.append("classification/status required for pattern claims")
        return result
    result.invariants.append({"family": "substrate", "status": "pass", "details": substrate_id})
    result.proof = {
        "claim_id": claim_id,
        "substrate_id": substrate_id,
        "surface": surface,
        "trace_id": payload.get("trace_id"),
        "law_id": "COLLECTIVE_PATTERN_LEDGER",
    }
    result.valid = True
    return result
