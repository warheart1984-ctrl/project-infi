"""Capability contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)


def validate_capability_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    trace_id = str(payload.get("trace_id") or "").strip()
    module = str(payload.get("module") or "").strip()
    action = str(payload.get("action") or "").strip()
    if not trace_id:
        result.errors.append("trace_id is required")
        return result
    if not module or not action:
        result.errors.append("module and action are required")
        return result
    if not payload.get("ok", True):
        result.errors.append("capability execution failed")
        return result
    result.invariants.append({"family": "capability_bridge", "status": "pass", "details": module})
    result.proof = {
        "trace_id": trace_id,
        "module": module,
        "action": action,
        "audit_sequence": payload.get("audit_sequence"),
        "law_id": "AAIS_CAPABILITY_MODULE_SPEC",
    }
    result.valid = True
    return result
