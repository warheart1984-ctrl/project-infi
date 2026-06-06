"""Cloud invariant contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)


def validate_invariant_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    mission_id = str(payload.get("mission_id") or "").strip()
    invariant_digest = str(payload.get("invariant_digest") or "").strip()
    if not mission_id:
        result.errors.append("mission_id is required")
        return result
    if not invariant_digest or len(invariant_digest) < 16:
        result.errors.append("invariant_digest is required")
        return result
    if not payload.get("all_passed", True):
        result.errors.append("invariant set did not pass")
        return result
    result.invariants.append({"family": "cloud_invariants", "status": "pass", "details": mission_id})
    result.proof = {
        "mission_id": mission_id,
        "invariant_digest": invariant_digest,
        "invariant_version": payload.get("invariant_version"),
        "law_id": "URG_CLOUD_INVARIANTS",
    }
    result.valid = True
    return result
