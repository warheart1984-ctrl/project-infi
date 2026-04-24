"""Universal Language and Foundation Law enforcement for EvolveEngine."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from evolve_engine.schemas import EvolutionRequest
from src.aais_ul import build_ul_snapshot

if TYPE_CHECKING:
    from evolve_engine.backends.local_evolving_ai import ResolvedConstraints


CONTRACT_VERSION = "aais.evolve.ul.v1"
ALLOWED_STRATEGIES = {"local_search"}
FOUNDATION_LAW_SEQUENCE = (
    {
        "law_id": "law_1_admission_control",
        "title": "Admission Control Law",
        "core_principle": "Nothing enters without Forge approval.",
    },
    {
        "law_id": "law_2_execution_governance",
        "title": "Execution Governance Law",
        "core_principle": "One authority. One role. No drift.",
    },
    {
        "law_id": "law_3_observability",
        "title": "Observability Law",
        "core_principle": "Nothing happens without visibility.",
    },
    {
        "law_id": "law_4_violation_handling",
        "title": "Violation Handling Clause",
        "core_principle": "Violation stops execution. Containment prevents spread.",
    },
    {
        "law_id": "law_5_consistent_execution",
        "title": "Consistent Execution Law",
        "core_principle": "Execution must remain consistent, regardless of path.",
    },
    {
        "law_id": "law_6_adaptation_constraint",
        "title": "Adaptation Constraint Law",
        "core_principle": "Learning is allowed. Structural mutation is not.",
    },
)


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


def _origin_status(request: EvolutionRequest) -> str:
    if request.jarvis_run_id:
        return "jarvis_authorized_candidate"
    return "external_candidate"


def _clamp_summary(request: EvolutionRequest, constraints: ResolvedConstraints) -> dict[str, Any]:
    requested = request.constraints
    return {
        "population_size": {
            "requested": requested.population_size,
            "applied": constraints.population_size,
            "clamped": requested.population_size is not None and requested.population_size != constraints.population_size,
        },
        "max_generations": {
            "requested": requested.max_generations,
            "applied": constraints.max_generations,
            "clamped": requested.max_generations is not None and requested.max_generations != constraints.max_generations,
        },
        "max_evaluations": {
            "requested": requested.max_evaluations,
            "applied": constraints.max_evaluations,
            "clamped": requested.max_evaluations is not None and requested.max_evaluations != constraints.max_evaluations,
        },
        "max_wall_time_seconds": {
            "requested": requested.max_wall_time_seconds,
            "applied": constraints.max_wall_time_seconds,
            "clamped": requested.max_wall_time_seconds is not None
            and requested.max_wall_time_seconds != constraints.max_wall_time_seconds,
        },
    }


def build_request_contract(
    request: EvolutionRequest,
    *,
    constraints: ResolvedConstraints,
) -> dict[str, Any]:
    origin_status = _origin_status(request)
    forge_processed = bool(request.jarvis_run_id)
    strategy_allowed = request.config.strategy in ALLOWED_STRATEGIES
    clamp_summary = _clamp_summary(request, constraints)

    admission_detail = (
        "Candidate artifacts are admitted in evaluation-only containment. "
        "No adaptive artifact is operationally activated inside EvolveEngine."
    )
    governance_detail = (
        "EvolveEngine remains the single execution authority and only the bounded "
        "`local_search` strategy is permitted."
    )
    observability_detail = (
        "Every evolve request, decision, evaluation, and law outcome is recorded "
        "in the trace store."
    )
    violation_detail = (
        "Violations are blocked, contained, and recorded before adaptive output "
        "can proceed."
    )
    consistency_detail = (
        "Success and error paths return the same law-enforcement and UL envelope "
        "shape."
    )
    adaptation_detail = (
        "Only validated evaluation outcomes may influence future generations, and "
        "all adaptive outputs remain non-deployable until Forge approval."
    )

    law_checks = [
        _law_check(
            law_id="law_1_admission_control",
            title="Admission Control Law",
            core_principle="Nothing enters without Forge approval.",
            passed=True,
            status="evaluation_only",
            action="contain_for_evaluation",
            detail=admission_detail,
            metadata={
                "origin_status": origin_status,
                "forge_processed": forge_processed,
            },
        ),
        _law_check(
            law_id="law_2_execution_governance",
            title="Execution Governance Law",
            core_principle="One authority. One role. No drift.",
            passed=strategy_allowed,
            status="enforced" if strategy_allowed else "blocked",
            action="bounded_local_search_only",
            detail=governance_detail if strategy_allowed else "Requested strategy falls outside the bounded EvolveEngine role.",
            metadata={
                "requested_strategy": request.config.strategy,
                "allowed_strategies": sorted(ALLOWED_STRATEGIES),
            },
        ),
        _law_check(
            law_id="law_3_observability",
            title="Observability Law",
            core_principle="Nothing happens without visibility.",
            passed=True,
            status="enforced",
            action="trace_every_phase",
            detail=observability_detail,
        ),
        _law_check(
            law_id="law_4_violation_handling",
            title="Violation Handling Clause",
            core_principle="Violation stops execution. Containment prevents spread.",
            passed=strategy_allowed,
            status="armed" if strategy_allowed else "contained",
            action="block_and_record",
            detail=violation_detail if strategy_allowed else "Execution was contained before start because a governing law failed.",
        ),
        _law_check(
            law_id="law_5_consistent_execution",
            title="Consistent Execution Law",
            core_principle="Execution must remain consistent, regardless of path.",
            passed=True,
            status="enforced",
            action="uniform_envelope",
            detail=consistency_detail,
        ),
        _law_check(
            law_id="law_6_adaptation_constraint",
            title="Adaptation Constraint Law",
            core_principle="Learning is allowed. Structural mutation is not.",
            passed=True,
            status="enforced",
            action="validated_outcomes_only",
            detail=adaptation_detail,
        ),
    ]

    blocked = not strategy_allowed
    blocking_law_id = "law_2_execution_governance" if blocked else None
    blocking_message = (
        "EvolveEngine rejected that request because it exceeds the bounded local-search role."
        if blocked
        else None
    )

    contract = {
        "contract_version": CONTRACT_VERSION,
        "source_of_truth": "evolve_engine_service",
        "component_id": f"evolve_candidate:{request.job_id}",
        "execution_id": request.job_id,
        "provider_path": "forge_eval",
        "origin_integrity": {
            "origin_status": origin_status,
            "forge_processed": forge_processed,
            "admission_status": "rejected" if blocked else "evaluation_only",
            "evaluation_status": "rejected" if blocked else "pending",
            "rejection_reason": "unsupported_strategy" if blocked else None,
        },
        "execution_governance": {
            "authority_validation": True,
            "role_scope_validation": strategy_allowed,
            "action_permission_check": "evaluation_only",
            "authoritative_controller": "evolve_engine_service",
            "requested_strategy": request.config.strategy,
            "allowed_strategies": sorted(ALLOWED_STRATEGIES),
        },
        "observability": {
            "trace_record": True,
            "decision_record": True,
            "guardrail_evaluation": True,
            "provider_path": "forge_eval",
            "execution_metadata": True,
        },
        "consistency": {
            "response_schema_validation": True,
            "stream_event_validation": True,
            "route_consistency_check": True,
            "constraint_clamps": clamp_summary,
        },
        "adaptation_constraints": {
            "adaptation_source_validation": "validated_outcomes_only",
            "structural_integrity_check": strategy_allowed,
            "authority_boundary_check": True,
            "law_compliance_check": strategy_allowed,
            "validated_parent_pool_only": True,
            "requires_forge_approval": True,
            "deployment_status": "contained_until_forge_approval",
        },
        "violation_state": {
            "violation_recorded": blocked,
            "containment_state": "contained" if blocked else "armed",
            "blocking_law_id": blocking_law_id,
            "blocking_message": blocking_message,
        },
        "law_checks": law_checks,
    }
    return contract


def build_ul_contract_snapshot(contract: dict[str, Any], request: EvolutionRequest) -> dict[str, Any]:
    guardrail_state = {
        "status": "contained" if contract["violation_state"]["violation_recorded"] else "active",
        "summary": "Foundation laws enforced at the EvolveEngine boundary.",
        "pipeline_mode": "evolve_engine",
        "effective_pipeline": [
            "admission_control",
            "execution_governance",
            "observability",
            "violation_handling",
            "consistent_execution",
            "adaptation_constraints",
        ],
        "requested_pipeline": [
            "admission_control",
            "execution_governance",
            "observability",
            "violation_handling",
            "consistent_execution",
            "adaptation_constraints",
        ],
        "adaptive_zone": "candidate_mutation_only",
        "override_blocked": True,
        "protected_zones": [
            "authority_layers",
            "foundation_laws",
            "response_contract",
        ],
        "allowed_growth_zones": [
            "candidate_mutation",
            "population_selection",
            "forge_eval_scoring",
        ],
    }
    modules = [
        {
            "type": "runtime_context",
            "environment": "evolve_engine",
            "provider": "forge_eval",
            "mode": "bounded_search",
        },
        {
            "channel": "orchestration",
            "source_module": "evolve_engine",
            "label": "Admission Control",
            "content": contract["origin_integrity"]["admission_status"],
            "metadata": {
                "origin_status": contract["origin_integrity"]["origin_status"],
                "forge_processed": contract["origin_integrity"]["forge_processed"],
            },
        },
        {
            "channel": "browser",
            "source_module": "evolve_engine",
            "label": "Execution Governance",
            "content": "single authority: evolve_engine_service",
            "metadata": {
                "requested_strategy": request.config.strategy,
                "role_scope_validation": contract["execution_governance"]["role_scope_validation"],
            },
        },
        {
            "channel": "browser",
            "source_module": "evolve_engine",
            "label": "Consistent Execution",
            "content": "uniform success/error envelope",
            "metadata": contract["consistency"],
        },
        {
            "channel": "specialist",
            "source_module": "evolve_engine",
            "label": "Adaptation Constraints",
            "content": "validated outcomes only; Forge approval required before deployment",
            "metadata": {
                "requires_forge_approval": True,
                "validated_parent_pool_only": True,
                "candidate_field": request.evaluation.candidate_field,
            },
        },
    ]
    return build_ul_snapshot(modules=modules, guardrail_state=guardrail_state)


def finalize_contract_success(
    contract: dict[str, Any],
    *,
    best_score: float,
    generations_run: int,
    evaluations: int,
    validated_outcomes: int,
) -> dict[str, Any]:
    result = deepcopy(contract)
    result["origin_integrity"]["evaluation_status"] = "completed"
    result["adaptation_constraints"]["validated_outcomes"] = int(validated_outcomes)
    result["adaptation_constraints"]["best_score"] = float(best_score)
    result["observability"]["generations_run"] = int(generations_run)
    result["observability"]["evaluations"] = int(evaluations)
    result["violation_state"]["containment_state"] = "contained_until_forge_approval"
    return result


def finalize_contract_error(
    contract: dict[str, Any],
    *,
    error_code: str,
    message: str,
    law_id: str | None = None,
    severity: str = "high",
) -> dict[str, Any]:
    result = deepcopy(contract)
    result["origin_integrity"]["evaluation_status"] = "failed"
    result["violation_state"]["violation_recorded"] = True
    result["violation_state"]["containment_state"] = "contained"
    result["violation_state"]["blocking_law_id"] = law_id or result["violation_state"].get("blocking_law_id")
    result["violation_state"]["blocking_message"] = _clip_text(message)
    result["violation_state"]["severity"] = severity
    result["violation_state"]["error_code"] = error_code
    return result


def build_violation_record(
    contract: dict[str, Any],
    *,
    code: str,
    message: str,
    law_id: str,
    severity: str,
    containment_state: str = "contained",
) -> dict[str, Any]:
    return {
        "law_id": law_id,
        "severity": severity,
        "code": code,
        "message": _clip_text(message),
        "component_id": contract.get("component_id"),
        "execution_id": contract.get("execution_id"),
        "containment_state": containment_state,
    }


def _enforce_request_laws(*, context: dict[str, Any]) -> dict[str, Any]:
    request = context["request"]
    constraints = context["constraints"]
    contract = build_request_contract(request, constraints=constraints)
    ul_snapshot = build_ul_contract_snapshot(contract, request)
    blocked = bool(contract["violation_state"]["violation_recorded"])
    violation = None
    if blocked:
        violation = build_violation_record(
            contract,
            code="law_violation",
            message=contract["violation_state"]["blocking_message"] or "Foundation law enforcement blocked the evolve request.",
            law_id=contract["violation_state"]["blocking_law_id"] or "law_2_execution_governance",
            severity="high",
        )
    return {
        "allowed": not blocked,
        "law_enforcement": contract,
        "ul_snapshot": ul_snapshot,
        "violation": violation,
    }


def _enforce_adaptation_laws(
    *,
    artifact: Any,
    context: dict[str, Any],
) -> dict[str, Any]:
    contract = deepcopy(context["law_enforcement"])
    ranked = list(artifact or [])
    validated = [item for item in ranked if item.get("ok")]
    if validated:
        payload = {
            "allowed": True,
            "validated_parent_count": len(validated),
            "rejected_parent_count": max(0, len(ranked) - len(validated)),
            "selection_rule": "validated_outcomes_only",
        }
        return {
            "allowed": True,
            "parents": validated,
            "decision": payload,
            "violation": None,
            "law_enforcement": contract,
        }

    violation = build_violation_record(
        contract,
        code="law_violation",
        message="Adaptation halted because no validated outcomes were available for the next generation.",
        law_id="law_6_adaptation_constraint",
        severity="high",
    )
    return {
        "allowed": False,
        "parents": [],
        "decision": {
            "allowed": False,
            "validated_parent_count": 0,
            "rejected_parent_count": len(ranked),
            "selection_rule": "validated_outcomes_only",
        },
        "violation": violation,
        "law_enforcement": finalize_contract_error(
            contract,
            error_code="law_violation",
            message=violation["message"],
            law_id="law_6_adaptation_constraint",
            severity="high",
        ),
    }


def enforce_foundation_laws(
    *,
    artifact: Any,
    action: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    if action == "evolve_request":
        return _enforce_request_laws(context=context)
    if action == "adaptation_parent_pool":
        return _enforce_adaptation_laws(artifact=artifact, context=context)
    raise ValueError(f"Unsupported foundation-law action: {action}")
