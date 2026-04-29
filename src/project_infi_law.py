from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from src.aris_integration import ARIS_CONTRACT_VERSION, build_aris_enforcement
from src.aais_ul import build_ul_snapshot
from src.governance_layer import GovernanceLayer, governance_layer
from src.project_infi_state_machine import (
    CycleContext,
    CycleDisposition,
    ExecutionResult,
    ProjectInfiStateMachine,
    ProposedChange,
)
from src.run_ledger import RunLedger
from src.six_wards_guardrails import GuardrailState, GuardrailThresholds, ShieldWard


PROJECT_INFI_CONTRACT_VERSION = "aais.project_infi.ul.v1"
PROJECT_INFI_LAW_IDS = [
    "law_1_entry_governance",
    "law_2_action_governance",
    "law_3_outcome_governance",
    "law_4_record_governance",
    "law_5_observability",
    "law_6_fail_closed",
    "law_7_external_suggestion_admission",
    "law_8_aris_runtime_boundary",
    "law_9_non_copy_clause",
]
VERIFICATION_PASS_STATES = {"completed", "healthy", "passed", "success", "verified"}
CYCLE_SUCCESS_RESULTS = {
    ExecutionResult.SUCCESS.value.lower(),
    ExecutionResult.PARTIAL.value.lower(),
    ExecutionResult.OVERLOAD.value.lower(),
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clip_text(value: Any, *, limit: int = 220) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_cisiv_stage(value: Any, *, default: str = "implementation") -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "verify": "verification",
        "verified": "verification",
        "test": "verification",
        "build": "implementation",
        "implemented": "implementation",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in {"concept", "identity", "structure", "implementation", "verification"}:
        return normalized
    return default


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


def _normalize_external_suggestion_admission(details: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(details or {})
    raw_suggestion = payload.get("external_suggestion")
    if raw_suggestion is None:
        raw_suggestion = payload.get("external_input")

    usage_mode = str(
        payload.get("external_suggestion_usage")
        or payload.get("external_input_usage")
        or "reference"
    ).strip().lower() or "reference"
    usage_aliases = {
        "compare": "comparison",
        "compare_only": "comparison",
        "inspire": "inspiration",
        "admit": "adoption",
        "adopt": "adoption",
    }
    usage_mode = usage_aliases.get(usage_mode, usage_mode)

    present = bool(payload.get("external_suggestion_present"))
    source = str(payload.get("external_suggestion_source") or "").strip() or None
    suggestion_summary = _clip_text(payload.get("external_suggestion_summary"))

    if isinstance(raw_suggestion, dict):
        present = present or bool(raw_suggestion)
        source = source or (str(raw_suggestion.get("source") or "").strip() or None)
        suggestion_summary = suggestion_summary or _clip_text(
            raw_suggestion.get("summary")
            or raw_suggestion.get("content")
            or raw_suggestion.get("proposal")
        )
    elif raw_suggestion is not None:
        present = True
        suggestion_summary = suggestion_summary or _clip_text(raw_suggestion)

    admitted_form = payload.get("admitted_external_form")
    admitted_form_summary = _clip_text(admitted_form)
    law_filter_applied = bool(
        payload.get("law_filter_applied")
        or payload.get("external_suggestion_filtered")
        or payload.get("external_suggestion_law_filtered")
    )
    adoption_requested = bool(
        payload.get("external_suggestion_adoption_requested")
        or usage_mode == "adoption"
    )
    admitted_form_documented = bool(admitted_form_summary)

    if not present:
        status = "not_applicable"
    elif adoption_requested and law_filter_applied and admitted_form_documented:
        status = "admitted"
    elif adoption_requested:
        status = "blocked"
    else:
        status = "reference_only"

    return {
        "present": present,
        "usage_mode": usage_mode,
        "adoption_requested": adoption_requested,
        "law_filter_applied": law_filter_applied,
        "admitted_form_documented": admitted_form_documented,
        "status": status,
        "source": source,
        "suggestion_summary": suggestion_summary,
        "admitted_form_summary": admitted_form_summary,
    }


class ProjectInfiLaw:
    """Shared law substrate for repo actions, runtime actions, and verification."""

    def __init__(
        self,
        *,
        governance_controller: GovernanceLayer | None = None,
        run_ledger: RunLedger | None = None,
    ) -> None:
        self.governance = governance_controller or governance_layer
        self.run_ledger = run_ledger
        self.state_machine = ProjectInfiStateMachine()
        self._cycle_contexts: dict[str, CycleContext] = {}

    def bind_run_ledger(self, run_ledger: RunLedger) -> None:
        self.run_ledger = run_ledger

    def _cycle_key(self, contract: dict[str, Any]) -> str:
        scope = dict(contract.get("request_scope") or {})
        surface = str(scope.get("surface") or "runtime_action").strip() or "runtime_action"
        session_id = str(scope.get("session_id") or "").strip()
        target = str(scope.get("target") or scope.get("action_id") or surface).strip() or surface
        return f"{surface}:{session_id or target}"

    def _get_cycle_context(self, contract: dict[str, Any]) -> CycleContext:
        key = self._cycle_key(contract)
        ctx = self._cycle_contexts.get(key)
        if ctx is None:
            ctx = CycleContext(bound_flag=True)
            self._cycle_contexts[key] = ctx
        return ctx

    @staticmethod
    def _serialize_debt(debt: Any) -> dict[str, Any]:
        return {
            "trauma": int(getattr(debt, "trauma", 0) or 0),
            "desire": int(getattr(debt, "desire", 0) or 0),
            "truth": int(getattr(debt, "truth", 0) or 0),
            "coupling": int(getattr(debt, "coupling", 0) or 0),
            "scar": int(getattr(debt, "scar", 0) or 0),
            "total": int(getattr(debt, "total", 0) or 0),
        }

    def _snapshot_cycle_context(self, ctx: CycleContext) -> dict[str, Any]:
        return {
            "current_state": ctx.current_state,
            "prime_depth": int(ctx.prime_depth or 0),
            "debt": self._serialize_debt(ctx.debt),
            "risk_profile": int(ctx.risk_profile or 0),
            "stabilization_attempts": int(ctx.stabilization_attempts or 0),
            "pending_mutations": int(ctx.pending_mutations or 0),
            "bound_flag": bool(ctx.bound_flag),
            "fracture_mode": bool(ctx.fracture_mode),
            "mode": str(getattr(ctx, "mode", "NORMAL") or "NORMAL"),
            "operator_review_required": bool(getattr(ctx, "operator_review_required", False)),
            "next_check_at": (
                getattr(ctx, "next_check_at", None).isoformat()
                if getattr(ctx, "next_check_at", None)
                else None
            ),
            "last_ready_at": (
                getattr(ctx, "last_ready_at", None).isoformat()
                if getattr(ctx, "last_ready_at", None)
                else None
            ),
            "last_ttl_seconds": int(getattr(ctx, "last_ttl_seconds", 0) or 0),
            "wait_count": int(getattr(ctx, "wait_count", 0) or 0),
            "cycle_count": int(ctx.cycle_count or 0),
            "last_error": getattr(ctx.last_error, "value", None),
        }

    @staticmethod
    def _stage_cisiv_stage(event_name: str, default: str) -> str:
        mapping = {
            "gamma_legitimacy": "concept",
            "l1_verification": "verification",
            "1010_design_judgment": "structure",
            "1111_debt_reckoning": "implementation",
            "l2_final_truth": "verification",
            "admit": "implementation",
            "delta_stabilization": "verification",
            "chronos_ttl": default,
            "recovery_drift": default,
            "wait_recheck": default,
            "fracture_operator_review": default,
            "voss_binding": "implementation",
            "next_1000": default,
            "rejected_no_admission": default,
        }
        return mapping.get(str(event_name or "").strip(), default)

    @staticmethod
    def _cycle_status(cycle_result: dict[str, Any]) -> str:
        status = str(cycle_result.get("status") or "").strip().lower()
        if status:
            return status
        final_truth = cycle_result.get("final_truth")
        if final_truth is not None:
            return str(final_truth.status.value).strip().lower()
        return "unknown"

    @staticmethod
    def _cycle_truthful(cycle_result: dict[str, Any]) -> bool:
        final_truth = cycle_result.get("final_truth")
        if final_truth is None:
            return False
        return bool(final_truth.truthful)

    @staticmethod
    def _normalize_design_quality(value: Any, *, default: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = default
        return max(0.0, min(1.0, numeric))

    def _build_proposed_change(
        self,
        contract: dict[str, Any],
        *,
        action_status: str | None = None,
        summary: str | None = None,
        apply_result: dict[str, Any] | None = None,
        verification_evidence: dict[str, Any] | None = None,
    ) -> ProposedChange:
        scope = dict(contract.get("request_scope") or {})
        request_details = dict(contract.get("request_details") or {})
        repo_change = bool(scope.get("repo_change"))
        normalized_status = str(action_status or "completed").strip().lower() or "completed"
        evidence = self._normalize_verification_evidence(verification_evidence) if repo_change else {
            "provided": normalized_status in VERIFICATION_PASS_STATES,
            "passed": normalized_status in VERIFICATION_PASS_STATES,
            "summary": _clip_text(summary),
            "checks": [],
        }
        cycle_kind = "repo_change" if repo_change else str(scope.get("action_id") or "runtime_action").strip() or "runtime_action"
        design_quality = 0.9
        risk_level = "high" if repo_change else "medium"
        debt_pressure = 0
        evidence_present = bool(evidence.get("provided"))
        changed_files = list((apply_result or {}).get("changed_files") or [])
        preview = dict((apply_result or {}).get("preview") or {})

        if repo_change:
            file_count = int((apply_result or {}).get("file_count") or len(changed_files) or 0)
            debt_pressure = min(max(file_count - 1, 0), 6)
            design_quality = 0.94 if preview.get("ready_for_review", True) else 0.62
            if evidence.get("provided") and not evidence.get("passed"):
                design_quality = 0.2
            elif not evidence.get("provided"):
                design_quality = 0.88
            if file_count >= 12:
                risk_level = "critical"
            elif file_count >= 6:
                risk_level = "high"
        else:
            if normalized_status in {"overload", "overloaded"}:
                cycle_kind = "overload"
                design_quality = 0.82
                debt_pressure = 3
                risk_level = "high"
                evidence_present = False
            elif normalized_status in {"partial", "degraded"}:
                cycle_kind = "partial"
                design_quality = 0.78
                debt_pressure = 2
                evidence_present = False
            elif normalized_status in {"failed", "error", "blocked", "rejected"}:
                design_quality = 0.2
                risk_level = "high"
                evidence_present = False

        return ProposedChange(
            kind=cycle_kind,
            authority=str(scope.get("surface") or "project_infi").strip() or "project_infi",
            context_valid=contract.get("origin_integrity", {}).get("admission_status") == "approved",
            protected_access_requested=bool(request_details.get("protected_access_requested")),
            operator_approved=bool(request_details.get("operator_approved", True)),
            risk_level=risk_level,
            evidence_present=evidence_present,
            design_quality=self._normalize_design_quality(request_details.get("design_quality"), default=design_quality),
            debt_pressure=debt_pressure,
            external_influence=str(scope.get("surface") or "project_infi").strip() or "project_infi",
        )

    def _emit_cycle_stage_logs(
        self,
        *,
        contract: dict[str, Any],
        cycle_result: dict[str, Any],
        actor_id: str,
        actor_role: str,
        run_id: str | None = None,
    ) -> list[dict[str, Any]]:
        scope = dict(contract.get("request_scope") or {})
        default_stage = str(scope.get("cisiv_stage") or "implementation").strip() or "implementation"
        cycle_logs: list[dict[str, Any]] = []

        for entry in list(cycle_result.get("event_log") or []):
            event_name = str(entry.get("event") or "").strip()
            if not event_name:
                continue
            stage_cisiv = self._stage_cisiv_stage(event_name, default_stage)
            payload = {
                "surface": scope.get("surface"),
                "action_id": scope.get("action_id"),
                "target": scope.get("target"),
                "repo_change": bool(scope.get("repo_change")),
                "cisiv_stage": stage_cisiv,
                "cycle_key": self._cycle_key(contract),
                "cycle_status": self._cycle_status(cycle_result),
                **{key: value for key, value in dict(entry).items() if key != "event"},
            }
            reason = _clip_text(
                entry.get("summary")
                or entry.get("reason")
                or entry.get("status")
                or entry.get("execution_status")
                or entry.get("disposition")
                or event_name
            )
            event = self._record_governance_event(
                actor_id=actor_id,
                actor_role=actor_role,
                decision=event_name,
                reason=reason,
                payload=payload,
            )
            cycle_logs.append(dict(event))
            if run_id and self.run_ledger:
                self.run_ledger.append_step(
                    run_id,
                    {
                        "kind": f"project_infi_stage_{event_name}",
                        "title": f"Project Infi {event_name.replace('_', ' ')}",
                        "summary": reason,
                        "status": str(
                            entry.get("status")
                            or entry.get("execution_status")
                            or entry.get("disposition")
                            or "recorded"
                        ),
                        "cisiv_stage": stage_cisiv,
                        "meta": {
                            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                            "cycle_event": event_name,
                            "cycle_status": self._cycle_status(cycle_result),
                            **payload,
                        },
                    },
                )
        if run_id and self.run_ledger:
            self.run_ledger.attach_artifact(
                run_id,
                {
                    "kind": "project_infi_governed_cycle",
                    "label": "Project Infi governed cycle",
                    "payload": {
                        "status": self._cycle_status(cycle_result),
                        "truthful": self._cycle_truthful(cycle_result),
                        "stage_count": len(cycle_logs),
                        "cycle_key": self._cycle_key(contract),
                    },
                },
            )
        return cycle_logs

    def _run_governed_cycle(
        self,
        contract: dict[str, Any],
        *,
        actor_id: str,
        actor_role: str,
        action_status: str | None = None,
        summary: str | None = None,
        apply_result: dict[str, Any] | None = None,
        verification_evidence: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        ctx = self._get_cycle_context(contract)
        proposed = self._build_proposed_change(
            contract,
            action_status=action_status,
            summary=summary,
            apply_result=apply_result,
            verification_evidence=verification_evidence,
        )
        cycle_result = self.state_machine.run_cycle(ctx, proposed)
        stage_logs = self._emit_cycle_stage_logs(
            contract=contract,
            cycle_result=cycle_result,
            actor_id=actor_id,
            actor_role=actor_role,
            run_id=run_id,
        )
        legitimacy = cycle_result.get("legitimacy")
        final_truth = cycle_result.get("final_truth")
        debt = cycle_result.get("debt")
        return {
            "status": self._cycle_status(cycle_result),
            "truthful": self._cycle_truthful(cycle_result),
            "legitimacy": {
                "disposition": getattr(getattr(legitimacy, "disposition", None), "value", None),
                "allowed": bool(getattr(legitimacy, "allowed", False)),
                "reason": getattr(legitimacy, "reason", None),
            }
            if legitimacy is not None
            else None,
            "final_truth": {
                "status": getattr(getattr(final_truth, "status", None), "value", None),
                "truthful": bool(getattr(final_truth, "truthful", False)),
                "summary": getattr(final_truth, "summary", None),
            }
            if final_truth is not None
            else None,
            "debt": {
                "disposition": getattr(getattr(debt, "disposition", None), "value", None),
                "findings": list(getattr(debt, "findings", []) or []),
                "record": self._serialize_debt(getattr(debt, "record", None)),
            }
            if debt is not None
            else None,
            "carryover_state": self._snapshot_cycle_context(ctx),
            "stage_logs": stage_logs,
            "raw_event_log": list(cycle_result.get("event_log") or []),
        }

    def require_contract(
        self,
        *,
        surface: str,
        action_id: str,
        actor_id: str,
        actor_role: str,
        session_id: str | None = None,
        target: str | None = None,
        repo_change: bool = False,
        verification_plan: dict[str, Any] | None = None,
        run_id: str | None = None,
        cisiv_stage: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        normalized_surface = str(surface or "").strip().lower() or "runtime_action"
        normalized_action_id = str(action_id or "").strip()
        normalized_actor_id = str(actor_id or "").strip() or "system"
        normalized_actor_role = str(actor_role or "").strip() or "system"
        normalized_target = str(target or normalized_action_id or normalized_surface).strip()
        normalized_stage = _normalize_cisiv_stage(cisiv_stage, default="implementation")
        normalized_details = dict(details or {})
        normalized_plan = self._normalize_verification_plan(verification_plan)
        external_admission = _normalize_external_suggestion_admission(normalized_details)
        aris_enforcement = build_aris_enforcement(
            details=normalized_details,
            runtime_context="operator_runtime" if bool(repo_change) else "live_runtime",
            effectful=bool(repo_change or normalized_surface not in {"chat_turn", "workflow_shell"}),
            source=normalized_surface,
            packet_type="repo_change_execute" if bool(repo_change) else normalized_action_id,
        )
        missing: list[str] = []
        if not normalized_surface:
            missing.append("surface")
        if not normalized_action_id:
            missing.append("action_id")
        if not normalized_target:
            missing.append("target")
        if repo_change and not str(run_id or "").strip():
            missing.append("run_id")
        if repo_change and not self._verification_plan_exists(normalized_plan):
            missing.append("verification_plan")
        if external_admission["adoption_requested"] and not external_admission["law_filter_applied"]:
            missing.append("external_suggestion_law_filter")
        if external_admission["adoption_requested"] and not external_admission["admitted_form_documented"]:
            missing.append("admitted_external_form")
        if not aris_enforcement["non_copy_clause"]["allowed"]:
            missing.append("non_copy_clause")

        shield = ShieldWard().check(
            GuardrailState(
                core_identity={
                    "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                    "surface": normalized_surface,
                    "action_id": normalized_action_id,
                },
                protected_zone_touched=bool(missing),
            ),
            GuardrailThresholds(),
        )
        blocked = bool(missing) or not shield.passed
        blocking_message = (
            "Project Infi law blocked the request because the law context was missing or unverifiable: "
            + ", ".join(missing)
            if missing
            else shield.message
        )
        contract = {
            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
            "source_of_truth": "project_infi_law",
            "component_id": f"project_infi:{normalized_surface}",
            "execution_id": normalized_details.get("execution_id") or normalized_action_id,
            "project_infi_laws": list(PROJECT_INFI_LAW_IDS),
            "origin_integrity": {
                "origin_status": "project_infi_governed",
                "admission_status": "rejected" if blocked else "approved",
                "evaluation_status": "failed" if blocked else "passed",
                "rejection_reason": "missing_law_context" if blocked else None,
            },
            "execution_governance": {
                "authority_validation": not blocked,
                "role_scope_validation": True,
                "action_permission_check": "project_infi_shared_primitives",
                "authoritative_controller": "project_infi_law",
                "surface": normalized_surface,
                "action_id": normalized_action_id,
                "repo_change": bool(repo_change),
                "cisiv_stage": normalized_stage,
            },
            "observability": {
                "trace_record": True,
                "decision_record": True,
                "guardrail_evaluation": True,
                "runtime_event_log": True,
                "judgment_log": True,
                "last_event_id": None,
                "last_judgment_id": None,
            },
            "consistency": {
                "shared_primitives_required": True,
                "record_alignment_required": bool(repo_change),
                "verification_required": bool(repo_change),
                "fail_closed": True,
            },
            "adaptation_constraints": {
                "adaptive_behavior": "disabled",
                "operator_review_required": bool(repo_change),
                "deployment_status": "verification_required" if repo_change else "runtime_governed",
                "law_compliance_check": not blocked,
            },
            "violation_state": {
                "violation_recorded": blocked,
                "containment_state": "blocked" if blocked else "governed",
                "blocking_law_id": "law_6_fail_closed" if blocked else None,
                "blocking_message": blocking_message if blocked else None,
            },
            "request_scope": {
                "surface": normalized_surface,
                "action_id": normalized_action_id,
                "target": normalized_target,
                "session_id": str(session_id or "").strip() or None,
                "run_id": str(run_id or "").strip() or None,
                "repo_change": bool(repo_change),
                "cisiv_stage": normalized_stage,
            },
            "request_details": normalized_details,
            "external_suggestion_admission": {
                "status": external_admission["status"],
                "present": external_admission["present"],
                "usage_mode": external_admission["usage_mode"],
                "adoption_requested": external_admission["adoption_requested"],
                "law_filter_applied": external_admission["law_filter_applied"],
                "admitted_form_documented": external_admission["admitted_form_documented"],
                "source": external_admission["source"],
                "suggestion_summary": external_admission["suggestion_summary"],
                "admitted_form_summary": external_admission["admitted_form_summary"],
            },
            "aris_enforcement": aris_enforcement,
            "project_infi_layers": {
                "entry": {
                    "status": "blocked" if blocked else "passed",
                    "detail": (
                        f"Law context missing: {', '.join(missing)}."
                        if missing
                        else "Entry context is present and governed."
                    ),
                },
                "action": {
                    "status": "blocked" if blocked else "passed",
                    "detail": (
                        "Repo-changing execution remains verification-gated."
                        if repo_change
                        else "Runtime action is bound to the shared Project Infi law substrate."
                    ),
                },
                "outcome": {
                    "status": "pending",
                    "detail": (
                        "Repo-changing outcomes remain provisional until verification judgment exists."
                        if repo_change
                        else "Outcome will be updated after runtime execution completes."
                    ),
                },
                "record": {
                    "status": "blocked" if repo_change and not run_id else "pending",
                    "detail": (
                        "Canonical logbook alignment requires a durable run record."
                        if repo_change and not run_id
                        else "Record alignment will be checked during finalization."
                    ),
                },
            },
        }
        contract["law_checks"] = [
            _law_check(
                law_id="law_1_entry_governance",
                title="Entry Governance Law",
                core_principle="Nothing enters without enough law context to be governed.",
                passed=not blocked,
                status="blocked" if blocked else "enforced",
                action="entry_context_validation",
                detail=contract["project_infi_layers"]["entry"]["detail"],
                metadata={"missing": missing},
            ),
            _law_check(
                law_id="law_2_action_governance",
                title="Action Governance Law",
                core_principle="Actions must use the shared Project Infi substrate.",
                passed=not blocked,
                status="blocked" if blocked else "enforced",
                action="shared_action_governance",
                detail=contract["project_infi_layers"]["action"]["detail"],
                metadata={"repo_change": bool(repo_change), "cisiv_stage": normalized_stage},
            ),
            _law_check(
                law_id="law_3_outcome_governance",
                title="Outcome Governance Law",
                core_principle="Repo-changing success cannot finalize without verification.",
                passed=not repo_change or self._verification_plan_exists(normalized_plan),
                status="enforced" if not repo_change or self._verification_plan_exists(normalized_plan) else "blocked",
                action="verification_required_before_finalize",
                detail=contract["project_infi_layers"]["outcome"]["detail"],
                metadata={"verification_plan": normalized_plan},
            ),
            _law_check(
                law_id="law_4_record_governance",
                title="Record Governance Law",
                core_principle="Major system work must align to the canonical logbook.",
                passed=not repo_change or bool(run_id),
                status="enforced" if not repo_change or bool(run_id) else "blocked",
                action="record_alignment_validation",
                detail=contract["project_infi_layers"]["record"]["detail"],
                metadata={"run_id": str(run_id or "").strip() or None},
            ),
            _law_check(
                law_id="law_5_observability",
                title="Observability Law",
                core_principle="Runtime action and judgment traces must stay inspectable.",
                passed=True,
                status="enforced",
                action="structured_event_and_judgment_logging",
                detail="Project Infi attaches structured event and judgment logs to governed flows.",
            ),
            _law_check(
                law_id="law_6_fail_closed",
                title="Fail-Closed Law",
                core_principle="Missing or unverifiable law context stops the action before trust can drift.",
                passed=not blocked,
                status="blocked" if blocked else "armed",
                action="shield_guardrail_fail_closed",
                detail=shield.message if not blocked else blocking_message,
            ),
            _law_check(
                law_id="law_7_external_suggestion_admission",
                title="External Suggestion Admission Law",
                core_principle="External suggestions must pass the law filter and be documented in admitted form before they become system truth.",
                passed=(
                    not external_admission["present"]
                    or not external_admission["adoption_requested"]
                    or (
                        external_admission["law_filter_applied"]
                        and external_admission["admitted_form_documented"]
                    )
                ),
                status=(
                    "not_applicable"
                    if not external_admission["present"]
                    else "observed"
                    if not external_admission["adoption_requested"]
                    else "enforced"
                    if external_admission["law_filter_applied"]
                    and external_admission["admitted_form_documented"]
                    else "blocked"
                ),
                action="external_suggestion_admission_filter",
                detail=(
                    "No external suggestion is present on this request."
                    if not external_admission["present"]
                    else "External suggestion is present for comparison or pressure only and is not being adopted."
                    if not external_admission["adoption_requested"]
                    else "External suggestion passed the law filter and the admitted form is documented."
                    if external_admission["law_filter_applied"]
                    and external_admission["admitted_form_documented"]
                    else "External suggestion adoption is blocked until the law filter runs and the admitted form is documented."
                ),
                metadata={
                    "usage_mode": external_admission["usage_mode"],
                    "source": external_admission["source"],
                    "law_filter_applied": external_admission["law_filter_applied"],
                    "admitted_form_documented": external_admission["admitted_form_documented"],
                },
            ),
            _law_check(
                law_id="law_8_aris_runtime_boundary",
                title="ARIS Runtime Boundary Law",
                core_principle="ARIS enters AAIS only as a governed embedded runtime profile and may not self-authorize as a parallel service.",
                passed=aris_enforcement["status"] == "enforced",
                status="enforced" if aris_enforcement["status"] == "enforced" else "blocked",
                action="aris_embedded_runtime_boundary",
                detail=(
                    "ARIS is enforced through the shared AAIS bridge and Project Infi law substrate."
                    if aris_enforcement["status"] == "enforced"
                    else "ARIS boundary enforcement blocked this request before raw or private material could drift into authority."
                ),
                metadata={
                    "contract_version": ARIS_CONTRACT_VERSION,
                    "runtime_profile": aris_enforcement["runtime_profile"],
                    "execution_boundary": aris_enforcement["execution_boundary"],
                },
            ),
            _law_check(
                law_id="law_9_non_copy_clause",
                title="ARIS Non-Copy Clause",
                core_principle="Raw outside proposals and private runs stay local; only admitted, abstracted, or signature-only forms may move forward.",
                passed=aris_enforcement["non_copy_clause"]["allowed"],
                status="enforced" if aris_enforcement["non_copy_clause"]["allowed"] else "blocked",
                action="aris_non_copy_clause",
                detail=aris_enforcement["non_copy_clause"]["summary"],
                metadata={
                    "share_mode": aris_enforcement["non_copy_clause"]["share_mode"],
                    "raw_copy_requested": aris_enforcement["non_copy_clause"]["raw_copy_requested"],
                    "private_run_requested": aris_enforcement["non_copy_clause"]["private_run_requested"],
                    "raw_categories_requested": list(
                        aris_enforcement["non_copy_clause"]["raw_categories_requested"]
                    ),
                },
            ),
        ]
        ul_snapshot = self._build_ul_snapshot(
            contract=contract,
            details=normalized_details,
            verification_plan=normalized_plan,
            blocked=blocked,
        )
        if blocked:
            blocked_event = self._record_governance_event(
                actor_id=normalized_actor_id,
                actor_role=normalized_actor_role,
                decision="law_context_blocked",
                reason=blocking_message,
                payload={
                    "surface": normalized_surface,
                    "action_id": normalized_action_id,
                    "target": normalized_target,
                    "cisiv_stage": normalized_stage,
                    "missing": missing,
                    "repo_change": bool(repo_change),
                    "session_id": str(session_id or "").strip() or None,
                    "run_id": str(run_id or "").strip() or None,
                },
            )
            contract["observability"]["last_event_id"] = blocked_event.get("id")
            raise ValueError(blocking_message)
        return contract, ul_snapshot, normalized_plan

    def finalize_runtime_action(
        self,
        contract: dict[str, Any],
        *,
        action_status: str,
        summary: str,
        actor_id: str,
        actor_role: str,
        run_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        result = deepcopy(contract)
        normalized_status = str(action_status or "completed").strip().lower() or "completed"
        governed_cycle = self._run_governed_cycle(
            contract,
            actor_id=actor_id,
            actor_role=actor_role,
            action_status=normalized_status,
            summary=summary,
            run_id=run_id,
        )
        governed_status = governed_cycle["status"]
        truthful = governed_cycle["truthful"]
        passed = truthful and governed_status in CYCLE_SUCCESS_RESULTS
        outcome_detail = (
            governed_cycle.get("final_truth", {}).get("summary")
            if truthful and governed_status != ExecutionResult.SUCCESS.value.lower()
            else _clip_text(summary)
        )
        if not truthful:
            outcome_detail = (
                governed_cycle.get("final_truth", {}).get("summary")
                or "Project Infi rejected admission for this runtime action."
            )
        event = self._emit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            decision="runtime_action_completed" if truthful else "runtime_action_blocked",
            reason=outcome_detail,
            payload={
                "surface": result["request_scope"]["surface"],
                "action_id": result["request_scope"]["action_id"],
                "target": result["request_scope"]["target"],
                "status": normalized_status,
                "governed_status": governed_status,
                "truthful": truthful,
                "cisiv_stage": result["request_scope"]["cisiv_stage"],
                "repo_change": bool(result["request_scope"]["repo_change"]),
                "run_id": str(run_id or "").strip() or None,
                "carryover_state": governed_cycle["carryover_state"],
                **dict(details or {}),
            },
            run_id=run_id,
        )
        result["project_infi_layers"]["outcome"] = {
            "status": "passed" if passed else "blocked",
            "detail": outcome_detail,
            "governed_status": governed_status,
        }
        result["project_infi_layers"]["record"] = {
            "status": "aligned",
            "detail": "Structured runtime event log recorded.",
        }
        result["governed_cycle"] = governed_cycle
        result["observability"]["last_event_id"] = event.get("id")
        result["observability"]["cycle_stage_logs"] = governed_cycle["stage_logs"]
        result["violation_state"]["violation_recorded"] = not passed
        result["violation_state"]["containment_state"] = "governed" if passed else "runtime_blocked"
        result["violation_state"]["blocking_law_id"] = None if passed else "law_2_action_governance"
        result["violation_state"]["blocking_message"] = None if passed else outcome_detail
        return result, event

    def finalize_repo_change(
        self,
        contract: dict[str, Any],
        *,
        apply_result: dict[str, Any],
        actor_id: str,
        actor_role: str,
        run_id: str,
        verification_evidence: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
        if not self.run_ledger:
            raise ValueError("Project Infi law requires a run ledger before repo changes can finalize.")
        run = self.run_ledger.get_run(run_id)
        if not run:
            raise ValueError("Project Infi law requires a durable run record before repo changes can finalize.")
        result = deepcopy(contract)
        evidence = self._normalize_verification_evidence(verification_evidence)
        governed_cycle = self._run_governed_cycle(
            contract,
            actor_id=actor_id,
            actor_role=actor_role,
            action_status="completed",
            summary=(apply_result or {}).get("summary"),
            apply_result=apply_result,
            verification_evidence=verification_evidence,
            run_id=run_id,
        )
        governed_status = governed_cycle["status"]
        truthful = governed_cycle["truthful"]
        verification_passed = truthful and evidence.get("passed", False)
        if not truthful:
            outcome_status = CycleDisposition.REJECTED_NO_ADMISSION.value
            outcome_detail = (
                governed_cycle.get("final_truth", {}).get("summary")
                or "Project Infi rejected admission for this repo change."
            )
        else:
            outcome_status = "completed" if verification_passed else "awaiting_verification"
            outcome_detail = (
                evidence.get("summary") or "Verification evidence approved this repo-changing action."
                if verification_passed
                else "Repo change applied, but Project Infi law is holding final success until verification evidence is recorded."
            )
        event = self._emit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            decision="repo_action_recorded",
            reason=outcome_detail,
            payload={
                "surface": result["request_scope"]["surface"],
                "action_id": result["request_scope"]["action_id"],
                "target": result["request_scope"]["target"],
                "status": outcome_status,
                "governed_status": governed_status,
                "truthful": truthful,
                "cisiv_stage": result["request_scope"]["cisiv_stage"],
                "repo_change": True,
                "run_id": run_id,
                "changed_files": list(apply_result.get("changed_files") or []),
                "file_count": int(apply_result.get("file_count") or 0),
                "verification_required": True,
                "verification_passed": verification_passed,
                "carryover_state": governed_cycle["carryover_state"],
            },
            run_id=run_id,
        )
        logbook_entry = self.run_ledger.append_step(
            run_id,
            {
                "kind": "project_infi_logbook",
                "title": "Project Infi canonical logbook",
                "summary": (
                    f"{apply_result.get('summary') or 'Repo change recorded.'} "
                    f"Governed cycle: {governed_status.replace('_', ' ')}. "
                    f"Finalization status: {outcome_status.replace('_', ' ')}."
                ),
                "status": outcome_status,
                "cisiv_stage": "verification" if verification_passed else "implementation",
                "meta": {
                    "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                    "action_id": result["request_scope"]["action_id"],
                    "review_id": apply_result.get("review_id"),
                    "changed_files": list(apply_result.get("changed_files") or []),
                    "governed_status": governed_status,
                    "truthful": truthful,
                    "verification_passed": verification_passed,
                    "cisiv_stage": "verification" if verification_passed else "implementation",
                },
            },
        )
        judgment_log = None
        if evidence.get("provided"):
            judgment_log = self.emit_judgment_log(
                review={
                    "source": "repo_change_verification",
                    "status": "advancing" if verification_passed else "blocked",
                    "score": 1.0 if verification_passed else 0.32,
                    "confidence": 0.86 if verification_passed else 0.74,
                    "summary": evidence.get("summary")
                    or (
                        "Verification evidence approved the repo-changing action."
                        if verification_passed
                        else "Verification evidence did not approve the repo-changing action."
                    ),
                    "suggested_mission_status": None if verification_passed else "blocked",
                },
                actor_id="project_infi_verifier",
                actor_role="system",
                session_id=result["request_scope"].get("session_id"),
                target=result["request_scope"]["target"],
                run_id=run_id,
            )
        result["project_infi_layers"]["outcome"] = {
            "status": "passed" if verification_passed else ("awaiting_verification" if truthful else "blocked"),
            "detail": outcome_detail,
            "governed_status": governed_status,
        }
        result["project_infi_layers"]["record"] = {
            "status": "aligned",
            "detail": "Canonical logbook entry appended to the run ledger.",
        }
        result["governed_cycle"] = governed_cycle
        result["observability"]["last_event_id"] = event.get("id")
        result["observability"]["cycle_stage_logs"] = governed_cycle["stage_logs"]
        result["observability"]["last_judgment_id"] = (judgment_log or {}).get("judgment_id")
        result["violation_state"]["violation_recorded"] = not verification_passed
        result["violation_state"]["containment_state"] = (
            "governed"
            if verification_passed
            else ("awaiting_verification" if truthful else CycleDisposition.REJECTED_NO_ADMISSION.value)
        )
        result["violation_state"]["blocking_law_id"] = (
            None if verification_passed else ("law_3_outcome_governance" if truthful else "law_2_action_governance")
        )
        result["violation_state"]["blocking_message"] = None if verification_passed else outcome_detail
        return result, event, judgment_log, logbook_entry

    def emit_judgment_log(
        self,
        *,
        review: dict[str, Any],
        actor_id: str,
        actor_role: str,
        session_id: str | None = None,
        target: str | None = None,
        run_id: str | None = None,
    ) -> dict[str, Any]:
        judgment = {
            "judgment_id": None,
            "judgment_type": "verification_judgment",
            "contract_version": PROJECT_INFI_CONTRACT_VERSION,
            "source": str(review.get("source") or "verification").strip(),
            "status": str(review.get("status") or "mixed").strip(),
            "score": review.get("score"),
            "confidence": review.get("confidence"),
            "summary": _clip_text(review.get("summary")),
            "suggested_mission_status": review.get("suggested_mission_status"),
            "target": str(target or review.get("target") or review.get("source") or "verification").strip(),
            "session_id": str(session_id or "").strip() or None,
            "cisiv_stage": "verification",
            "reviewed_at": str(review.get("reviewed_at") or _utc_now_iso()),
        }
        event = self._emit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            decision="verification_judgment_logged",
            reason=judgment["summary"] or "Project Infi recorded a verification judgment.",
            payload=judgment,
            run_id=run_id,
        )
        judgment["judgment_id"] = event.get("id")
        return judgment

    def _emit_event(
        self,
        *,
        actor_id: str,
        actor_role: str,
        decision: str,
        reason: str,
        payload: dict[str, Any],
        run_id: str | None = None,
    ) -> dict[str, Any]:
        event = self._record_governance_event(
            actor_id=actor_id,
            actor_role=actor_role,
            decision=decision,
            reason=reason,
            payload=payload,
        )
        if run_id and self.run_ledger:
            self.run_ledger.attach_artifact(
                run_id,
                {
                    "kind": "project_infi_event",
                    "label": "Project Infi law event",
                    "payload": {
                        "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                        "event": dict(event),
                    },
                },
            )
        return event

    def _record_governance_event(
        self,
        *,
        actor_id: str,
        actor_role: str,
        decision: str,
        reason: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return self.governance.record_module_event(
            actor_id=actor_id,
            actor_role=actor_role,
            module_id="project_infi_law",
            decision=decision,
            reason=reason,
            details={
                "contract_version": PROJECT_INFI_CONTRACT_VERSION,
                **dict(payload or {}),
            },
        )

    def _normalize_verification_plan(self, verification_plan: dict[str, Any] | None) -> dict[str, Any]:
        plan = dict(verification_plan or {})
        plan["recommended_tests"] = [
            str(item).strip()
            for item in list(plan.get("recommended_tests") or [])
            if str(item).strip()
        ]
        plan["verification_checklist"] = [
            str(item).strip()
            for item in list(plan.get("verification_checklist") or [])
            if str(item).strip()
        ]
        return plan

    def _verification_plan_exists(self, verification_plan: dict[str, Any] | None) -> bool:
        plan = dict(verification_plan or {})
        return bool(list(plan.get("recommended_tests") or []) or list(plan.get("verification_checklist") or []))

    def _normalize_verification_evidence(self, evidence: dict[str, Any] | None) -> dict[str, Any]:
        payload = dict(evidence or {})
        status = str(payload.get("status") or "").strip().lower()
        passed = bool(payload.get("passed")) or status in VERIFICATION_PASS_STATES
        summary = _clip_text(payload.get("summary"))
        checks = [
            str(item).strip()
            for item in list(payload.get("checks") or payload.get("verification_checklist") or [])
            if str(item).strip()
        ]
        return {
            "provided": bool(payload),
            "status": status or ("passed" if passed else "not_provided"),
            "passed": passed,
            "summary": summary,
            "checks": checks,
        }

    def _build_ul_snapshot(
        self,
        *,
        contract: dict[str, Any],
        details: dict[str, Any],
        verification_plan: dict[str, Any],
        blocked: bool,
    ) -> dict[str, Any]:
        summary = (
            f"Project Infi law is governing {contract['request_scope']['action_id']} on "
            f"{contract['request_scope']['target']} through entry, action, outcome, and record layers."
        )
        return build_ul_snapshot(
            modules=[
                {
                    "source_module": "project_infi_law",
                    "channel": "instruction",
                    "label": "Project Infi law contract",
                    "content": summary,
                    "metadata": {
                        "surface": contract["request_scope"]["surface"],
                        "action_id": contract["request_scope"]["action_id"],
                        "repo_change": contract["request_scope"]["repo_change"],
                        "cisiv_stage": contract["request_scope"]["cisiv_stage"],
                    },
                },
                {
                    "source_module": "project_infi_law",
                    "channel": "runtime",
                    "label": "Project Infi runtime context",
                    "content": (
                        f"target={contract['request_scope']['target']} "
                        f"session={contract['request_scope'].get('session_id') or 'none'} "
                        f"run={contract['request_scope'].get('run_id') or 'none'}"
                    ),
                    "metadata": {
                        "details": dict(details or {}),
                        "verification_plan": dict(verification_plan or {}),
                    },
                },
            ],
            guardrail_state={
                "status": "blocked" if blocked else "nominal",
                "summary": (
                    "Project Infi law blocked the request before execution."
                    if blocked
                    else "Project Infi law context is present and inspectable."
                ),
                "pipeline_mode": "project_infi_law",
                "effective_pipeline": ["entry", "action", "outcome", "record"],
                "requested_pipeline": [contract["request_scope"]["surface"]],
                "adaptive_zone": "governed",
                "override_blocked": blocked,
                "protected_zones": ["project_infi_law"],
                "allowed_growth_zones": ["verification_evidence", "runtime_event_log"],
            },
        )
