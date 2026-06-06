"""Workflow contribution validator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidityResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    invariants: list[dict[str, str]] = field(default_factory=list)
    proof: dict[str, Any] = field(default_factory=dict)


def validate_workflow_contribution(
    payload: dict[str, Any],
    *,
    tenant_id: str,
    operator_id: str,
    aais_instance_id: str,
    constraints: dict[str, Any] | None = None,
) -> ValidityResult:
    result = ValidityResult(valid=False)
    workflow_id = str(payload.get("workflow_id") or "").strip()
    run_id = str(payload.get("run_id") or "").strip()
    if not workflow_id:
        result.errors.append("workflow_id is required")
        return result
    if not run_id:
        result.errors.append("run_id is required")
        return result
    if payload.get("dry_run"):
        result.errors.append("dry_run workflows are not rewardable")
        return result
    step_count = int(payload.get("step_count") or 0)
    if step_count <= 0:
        result.errors.append("step_count must be positive")
        return result
    result.invariants.append({"family": "workflow_chain", "status": "pass", "details": workflow_id})
    result.proof = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "step_count": step_count,
        "law_id": "AAIS_WORKFLOW_FAMILY_ORGANS_LAW",
    }
    result.valid = True
    return result
