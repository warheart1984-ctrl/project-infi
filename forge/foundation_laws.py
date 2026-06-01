"""Foundation-law envelope for the isolated Forge contractor lane."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "aais.forge.ul.v1"
FOUNDATION_LAW_IDS = [
    "law_1_admission_control",
    "law_2_execution_governance",
    "law_3_observability",
    "law_4_violation_handling",
    "law_5_consistent_execution",
    "law_6_adaptation_constraint",
]


def _clip_text(value: Any, *, limit: int = 180) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _law_check(
    *,
    law_id: str,
    title: str,
    core_principle: str,
    passed: bool,
    status: str,
    action: str,
    detail: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "law_id": law_id,
        "title": title,
        "core_principle": core_principle,
        "passed": bool(passed),
        "status": status,
        "action": action,
        "detail": detail,
        "metadata": dict(metadata or {}),
    }


def _context_dict(context: dict[str, Any] | None) -> dict[str, Any]:
    return dict(context or {})


def default_error_law_id(code: str) -> str:
    mapping = {
        "invalid_request": "law_1_admission_control",
        "law_violation": "law_2_execution_governance",
        "model_error": "law_4_violation_handling",
        "invalid_json": "law_5_consistent_execution",
        "contract_violation": "law_5_consistent_execution",
    }
    return mapping.get(str(code or "").strip().lower(), "law_4_violation_handling")


def default_error_severity(code: str) -> str:
    mapping = {
        "invalid_request": "high",
        "law_violation": "high",
        "model_error": "high",
        "invalid_json": "high",
        "contract_violation": "high",
    }
    return mapping.get(str(code or "").strip().lower(), "high")


def build_request_contract(
    *,
    task_id: str,
    kind: str,
    context: dict[str, Any] | None,
    model: str,
    trace_enabled: bool,
) -> dict[str, Any]:
    normalized_context = _context_dict(context)
    review_gate_enabled = bool(normalized_context.get("no_execution_without_handoff", True))
    blocked = not review_gate_enabled
    raw_files = normalized_context.get("files") if isinstance(normalized_context.get("files"), list) else []
    raw_focus_files = (
        normalized_context.get("focus_files")
        if isinstance(normalized_context.get("focus_files"), list)
        else []
    )
    file_count = len(raw_files)
    focus_files = [str(item).strip() for item in raw_focus_files if str(item).strip()]
    provider_path = f"anthropic_contractor:{model}"
    blocking_message = (
        "Forge contractor remains review-gated. Direct execution without handoff is not permitted."
        if blocked
        else None
    )

    law_checks = [
        _law_check(
            law_id="law_1_admission_control",
            title="Admission Control Law",
            core_principle="Nothing enters without Forge approval.",
            passed=True,
            status="enforced",
            action="forge_preflight_normalization",
            detail=(
                "Forge accepted the request only after task-local preflight, secret screening, "
                "and bounded context normalization."
            ),
            metadata={
                "origin_status": "forge_normalized_request",
                "forge_processed": True,
                "file_count": file_count,
            },
        ),
        _law_check(
            law_id="law_2_execution_governance",
            title="Execution Governance Law",
            core_principle="One authority. One role. No drift.",
            passed=review_gate_enabled,
            status="enforced" if review_gate_enabled else "blocked",
            action="review_only_handoff_required",
            detail=(
                "Forge stays inside a review-first contractor role and never executes changes directly."
                if review_gate_enabled
                else "Forge blocked the request because it attempted to disable the required review gate."
            ),
            metadata={
                "requested_kind": str(kind or "").strip(),
                "review_gate_enabled": review_gate_enabled,
            },
        ),
        _law_check(
            law_id="law_3_observability",
            title="Observability Law",
            core_principle="Nothing happens without visibility.",
            passed=True,
            status="enforced",
            action="trace_every_request",
            detail="Forge records a bounded trace, law envelope, and UL snapshot for every request.",
            metadata={
                "trace_enabled": bool(trace_enabled),
                "provider_path": provider_path,
            },
        ),
        _law_check(
            law_id="law_4_violation_handling",
            title="Violation Handling Clause",
            core_principle="Violation stops execution. Containment prevents spread.",
            passed=review_gate_enabled,
            status="armed" if review_gate_enabled else "contained",
            action="block_and_contain",
            detail=(
                "Forge errors and contract violations are returned in a contained review-only envelope."
                if review_gate_enabled
                else "Execution was contained before model access because governance law enforcement failed."
            ),
        ),
        _law_check(
            law_id="law_5_consistent_execution",
            title="Consistent Execution Law",
            core_principle="Execution must remain consistent, regardless of path.",
            passed=True,
            status="enforced",
            action="uniform_success_error_envelope",
            detail="Success and error paths both emit the same law-enforcement and UL envelope shape.",
        ),
        _law_check(
            law_id="law_6_adaptation_constraint",
            title="Adaptation Constraint Law",
            core_principle="Learning is allowed. Structural mutation is not.",
            passed=True,
            status="disabled",
            action="no_runtime_adaptation",
            detail="Forge contractor requests do not adapt or self-mutate during execution.",
        ),
    ]

    return {
        "contract_version": CONTRACT_VERSION,
        "source_of_truth": "forge_service",
        "component_id": f"forge_task:{task_id}",
        "execution_id": task_id,
        "provider_path": provider_path,
        "origin_integrity": {
            "origin_status": "forge_normalized_request",
            "forge_processed": True,
            "admission_status": "rejected" if blocked else "approved",
            "evaluation_status": "rejected" if blocked else "passed",
            "rejection_reason": "direct_execution_disabled" if blocked else None,
        },
        "execution_governance": {
            "authority_validation": True,
            "role_scope_validation": review_gate_enabled,
            "action_permission_check": (
                "review_only_handoff_required"
                if review_gate_enabled
                else "blocked_direct_execution_request"
            ),
            "authoritative_controller": "forge_service",
            "requested_kind": str(kind or "").strip(),
            "review_gate_enabled": review_gate_enabled,
        },
        "observability": {
            "trace_record": True,
            "decision_record": True,
            "guardrail_evaluation": True,
            "provider_path": provider_path,
            "execution_metadata": True,
            "trace_enabled": bool(trace_enabled),
        },
        "consistency": {
            "response_schema_validation": True,
            "stream_event_validation": True,
            "route_consistency_check": True,
            "non_streaming_envelope": True,
        },
        "adaptation_constraints": {
            "adaptation_source_validation": "adaptive_behavior_disabled",
            "structural_integrity_check": True,
            "authority_boundary_check": review_gate_enabled,
            "law_compliance_check": review_gate_enabled,
            "adaptive_behavior": "disabled",
            "operator_review_required": True,
            "deployment_status": "review_only_handoff",
        },
        "violation_state": {
            "violation_recorded": blocked,
            "containment_state": "contained" if blocked else "review_only_handoff",
            "blocking_law_id": "law_2_execution_governance" if blocked else None,
            "blocking_message": blocking_message,
        },
        "law_checks": law_checks,
        "request_scope": {
            "goal": _clip_text(normalized_context.get("goal")),
            "file_count": file_count,
            "focus_files": focus_files[:6],
        },
    }


def finalize_contract_success(
    contract: dict[str, Any],
    *,
    trace_id: str,
) -> dict[str, Any]:
    result = deepcopy(contract)
    result["observability"]["trace_id"] = trace_id
    result["violation_state"]["containment_state"] = "review_only_handoff"
    result["violation_state"]["violation_recorded"] = False
    return result


def finalize_contract_error(
    contract: dict[str, Any],
    *,
    error_code: str,
    message: str,
    law_id: str,
    severity: str,
) -> dict[str, Any]:
    result = deepcopy(contract)
    normalized_code = str(error_code or "").strip().lower()
    result["origin_integrity"]["evaluation_status"] = "failed"
    if normalized_code in {"invalid_request", "law_violation"}:
        result["origin_integrity"]["admission_status"] = "rejected"
        result["origin_integrity"]["rejection_reason"] = law_id
    result["violation_state"]["violation_recorded"] = True
    result["violation_state"]["containment_state"] = "contained"
    result["violation_state"]["blocking_law_id"] = law_id
    result["violation_state"]["blocking_message"] = _clip_text(message)
    result["violation_state"]["severity"] = severity
    result["violation_state"]["error_code"] = error_code

    for item in result.get("law_checks") or []:
        if item.get("law_id") == law_id:
            item["passed"] = False
            item["status"] = "blocked"
            item["detail"] = _clip_text(message)
    return result


def build_ul_contract_snapshot(
    contract: dict[str, Any],
    *,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_context = _context_dict(context)
    raw_files = normalized_context.get("files") if isinstance(normalized_context.get("files"), list) else []
    raw_focus_files = (
        normalized_context.get("focus_files")
        if isinstance(normalized_context.get("focus_files"), list)
        else []
    )
    raw_excluded_files = (
        normalized_context.get("excluded_files")
        if isinstance(normalized_context.get("excluded_files"), list)
        else []
    )
    payloads = [
        {
            "source": "forge_runtime",
            "kind": "context",
            "section": "runtime_context",
            "data": {
                "environment": "forge",
                "provider": contract.get("provider_path"),
                "mode": "bounded_contractor",
            },
            "metadata": {"contract_version": contract.get("contract_version")},
        },
        {
            "source": "forge_runtime",
            "kind": "mission",
            "section": "mission_context",
            "data": {
                "goal": normalized_context.get("goal"),
                "requested_kind": contract.get("execution_governance", {}).get("requested_kind"),
                "review_gate_enabled": contract.get("execution_governance", {}).get("review_gate_enabled"),
            },
            "metadata": {},
        },
        {
            "source": "forge_runtime",
            "kind": "workspace",
            "section": "workspace_context",
            "data": {
                "file_count": len(raw_files),
                "focus_files": list(raw_focus_files)[:6],
                "target_scope": normalized_context.get("target_scope"),
            },
            "metadata": {
                "excluded_files": list(raw_excluded_files)[:6],
            },
        },
        {
            "source": "forge_runtime",
            "kind": "trace",
            "section": "protocol_trace",
            "data": {
                "authority_validation": contract.get("execution_governance", {}).get("authority_validation"),
                "role_scope_validation": contract.get("execution_governance", {}).get("role_scope_validation"),
                "trace_record": contract.get("observability", {}).get("trace_record"),
            },
            "metadata": {
                "provider_path": contract.get("observability", {}).get("provider_path"),
            },
        },
        {
            "source": "forge_runtime",
            "kind": "guardrail",
            "section": "guardrail_state",
            "data": {
                "status": (
                    "blocked"
                    if contract.get("violation_state", {}).get("violation_recorded")
                    else "active"
                ),
                "summary": "Foundation laws enforced at the Forge contractor boundary.",
                "pipeline_mode": "forge_contract",
                "effective_pipeline": [
                    "admission_control",
                    "execution_governance",
                    "observability",
                    "violation_handling",
                    "consistent_execution",
                    "review_handoff",
                ],
                "requested_pipeline": [
                    "admission_control",
                    "execution_governance",
                    "observability",
                    "violation_handling",
                    "consistent_execution",
                    "review_handoff",
                ],
                "adaptive_zone": "disabled",
                "override_blocked": True,
            },
            "metadata": {
                "protected_zones": [
                    "contractor_boundary",
                    "authority_layers",
                    "review_gate",
                    "response_contract",
                ],
                "allowed_growth_zones": [
                    "task_local_generation",
                    "proposal_authoring",
                ],
            },
        },
    ]
    sections: list[str] = []
    for payload in payloads:
        section = payload.get("section")
        if section and section not in sections:
            sections.append(section)
    return {
        "count": len(payloads),
        "sections": sections,
        "payloads": payloads,
    }
