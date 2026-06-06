"""Bridge OTEM workflow handoffs into workflow_approvals and substrate execution."""

# Mythic: Otem Execution Approval Bridge
# Engineering: OtemExecutionApprovalBridgeEngine
from __future__ import annotations

import json
from typing import Any

from app.db import (
    create_workflow_approval,
    create_workflow_run,
    get_workflow,
    get_workflow_run,
    list_pending_workflow_approvals,
    now_iso,
    update_workflow_approval,
    update_workflow_run,
)
from app.db import get_conn
from app.workflow_validation import build_workflow_config_from_graph
from src.cisiv import normalize_cisiv_stage
from src.otem_execution_substrate import get_otem_execution_substrate

OTEM_EXECUTION_SHELL_WORKFLOW_ID = "otem-execution-substrate"
OTEM_EXECUTION_STEP_ID = "otem-exec-approval"
OTEM_EXECUTION_STEP_TYPE = "otem_execution_substrate"
OTEM_EXECUTION_STEP_LABEL = "OTEM execution approval"


def _shell_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {
                "label": "OTEM Trigger",
                "kind": "trigger",
                "subtype": "manual",
                "config": {},
            },
        },
        {
            "id": OTEM_EXECUTION_STEP_ID,
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": OTEM_EXECUTION_STEP_LABEL,
                "kind": "action",
                "subtype": "task.create",
                "config": {},
            },
        },
    ]
    edges = [
        {
            "id": "edge-1",
            "source": "trigger-1",
            "target": OTEM_EXECUTION_STEP_ID,
        },
    ]
    return nodes, edges


def ensure_otem_execution_shell_workflow() -> dict[str, Any]:
    """Ensure the fixed shell workflow row exists for OTEM execution approvals."""
    existing = get_workflow(OTEM_EXECUTION_SHELL_WORKFLOW_ID)
    if existing:
        return existing

    nodes, edges = _shell_graph()
    config = build_workflow_config_from_graph("OTEM Execution Substrate", nodes, edges)
    ts = now_iso()
    cisiv_stage = normalize_cisiv_stage("structure")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO workflows (
                id, name, active, nodes_json, edges_json, config_json, cisiv_stage, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                OTEM_EXECUTION_SHELL_WORKFLOW_ID,
                "OTEM Execution Substrate",
                1,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                cisiv_stage,
                ts,
                ts,
            ),
        )
    workflow = get_workflow(OTEM_EXECUTION_SHELL_WORKFLOW_ID)
    if workflow is None:
        raise RuntimeError("Failed to create OTEM execution shell workflow")
    return workflow


def _find_pending_otem_approval(
    session_id: str,
    workflow_template_id: str | None,
) -> dict[str, Any] | None:
    for approval in list_pending_workflow_approvals(limit=200):
        if str(approval.get("step_type") or "") != OTEM_EXECUTION_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        if str(payload.get("otem_session_id") or "") != session_id:
            continue
        if workflow_template_id and str(payload.get("workflow_template_id") or "") != workflow_template_id:
            continue
        return approval
    return None


def _build_paused_run_output(
    *,
    session_id: str,
    otem_execution_workflow_id: str,
    handoff: dict[str, Any],
) -> dict[str, Any]:
    template_name = handoff.get("template_name") or handoff.get("workflow_template_id") or "OTEM"
    return {
        "workflowName": "OTEM Execution Substrate",
        "trigger": {"type": "manual", "label": "OTEM handoff"},
        "totalSteps": 1,
        "currentStep": 1,
        "currentStepLabel": OTEM_EXECUTION_STEP_LABEL,
        "nextStepIndex": 0,
        "plannedSteps": [
            {
                "stepId": OTEM_EXECUTION_STEP_ID,
                "label": f"OTEM: {template_name}",
                "type": OTEM_EXECUTION_STEP_TYPE,
                "order": 1,
                "status": "awaiting_approval",
                "output": None,
                "error": None,
            },
        ],
        "otem_session_id": session_id,
        "otem_execution_workflow_id": otem_execution_workflow_id,
        "message": "Paused for OTEM execution operator approval.",
    }


def maybe_enqueue_otem_execution_approval(
    session_id: str | None,
    otem_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Enqueue a workflow approval when a session-bound OTEM turn has a workflow handoff."""
    normalized_session = str(session_id or "").strip()
    result = dict(otem_result or {})
    handoff = result.get("workflow_handoff")
    if not normalized_session or not isinstance(handoff, dict) or not handoff:
        return None
    if str(result.get("status") or "").strip().lower() == "rejected":
        return None

    template_id = str(handoff.get("workflow_template_id") or "").strip() or None
    existing = _find_pending_otem_approval(normalized_session, template_id)
    if existing:
        payload = dict(existing.get("payload") or {})
        return {
            "approval_id": existing["id"],
            "workflow_run_id": existing["workflow_run_id"],
            "otem_execution_workflow_id": payload.get("otem_execution_workflow_id"),
            "status": "pending",
            "deduped": True,
        }

    ensure_otem_execution_shell_workflow()
    substrate = get_otem_execution_substrate()
    proposal = {
        "summary": str(
            handoff.get("rationale")
            or result.get("restated_task")
            or result.get("task")
            or ""
        )[:500],
        "objective": str(result.get("restated_task") or result.get("task") or "")[:500],
        "session_id": normalized_session,
        "workflow_template_id": template_id,
        "handoff": handoff,
        "plan": [dict(step or {}) for step in list(result.get("plan") or [])],
    }
    substrate_record = substrate.create_proposal(proposal, runtime_context="operator_runtime")
    otem_execution_workflow_id = str(substrate_record["workflow_id"])

    run_output = _build_paused_run_output(
        session_id=normalized_session,
        otem_execution_workflow_id=otem_execution_workflow_id,
        handoff=handoff,
    )
    run_record = create_workflow_run(
        OTEM_EXECUTION_SHELL_WORKFLOW_ID,
        "awaiting_approval",
        run_output,
        cisiv_stage="implementation",
    )
    if run_record is None:
        raise RuntimeError("Failed to create OTEM execution workflow run")

    approval = create_workflow_approval(
        workflow_run_id=run_record["id"],
        workflow_id=OTEM_EXECUTION_SHELL_WORKFLOW_ID,
        step_id=OTEM_EXECUTION_STEP_ID,
        step_label=f"OTEM: {handoff.get('template_name') or template_id or 'execution'}",
        step_type=OTEM_EXECUTION_STEP_TYPE,
        reason=str(handoff.get("rationale") or "OTEM workflow handoff requires operator approval before execution."),
        payload={
            "otem_execution_workflow_id": otem_execution_workflow_id,
            "otem_session_id": normalized_session,
            "workflow_template_id": template_id,
            "handoff": handoff,
            "proposal_summary": proposal.get("summary"),
            "cisiv_stage": "implementation",
        },
        cisiv_stage="implementation",
    )
    if approval is None:
        raise RuntimeError("Failed to create OTEM execution workflow approval")

    try:
        from src.operator_decision_ledger import append_otem_approval_event

        append_otem_approval_event(
            normalized_session,
            approval_id=str(approval["id"]),
            decision="pending",
            handoff=handoff,
            governed_pipeline=dict(result.get("governed_pipeline") or {}),
        )
    except Exception:
        pass

    return {
        "approval_id": approval["id"],
        "workflow_run_id": run_record["id"],
        "otem_execution_workflow_id": otem_execution_workflow_id,
        "status": "pending",
        "deduped": False,
    }


def _substrate_workflow_exists(otem_execution_workflow_id: str) -> bool:
    substrate = get_otem_execution_substrate()
    try:
        substrate.get_workflow(otem_execution_workflow_id)
        return True
    except KeyError:
        return False


def resolve_otem_execution_approval(approval: dict[str, Any], action: str) -> dict[str, Any]:
    """Approve or reject an OTEM execution substrate approval without Celery resume."""
    if str(approval.get("step_type") or "") != OTEM_EXECUTION_STEP_TYPE:
        raise ValueError("Approval is not an OTEM execution substrate approval")

    payload = dict(approval.get("payload") or {})
    workflow_run_id = str(approval.get("workflow_run_id") or "")
    run_record = get_workflow_run(workflow_run_id) or {}
    otem_execution_workflow_id = str(payload.get("otem_execution_workflow_id") or "")

    if action == "reject":
        update_workflow_approval(approval["id"], "rejected")
        output = dict(run_record.get("output") or {})
        output.update(
            {
                "error": f"Approval rejected for step: {approval.get('step_label')}",
                "message": f"Approval rejected for step: {approval.get('step_label')}",
                "rejectedAt": now_iso(),
            }
        )
        update_workflow_run(workflow_run_id, status="failed", output=output)
        try:
            from src.operator_decision_ledger import append_otem_approval_event

            append_otem_approval_event(
                str(payload.get("otem_session_id") or ""),
                approval_id=str(approval["id"]),
                decision="reject",
                handoff=dict(payload.get("handoff") or {}),
            )
        except Exception:
            pass
        return {"ok": True, "status": "rejected", "substrate": None}

    if action != "approve":
        raise ValueError(f"Unsupported approval action: {action}")

    if not otem_execution_workflow_id:
        raise ValueError("Missing otem_execution_workflow_id in approval payload")

    if not _substrate_workflow_exists(otem_execution_workflow_id):
        raise KeyError(
            "OTEM execution workflow not found in this process (stale after restart). "
            "Reject this approval and re-run the OTEM handoff in the same session."
        )

    session_id = str(payload.get("otem_session_id") or "")
    handoff = dict(payload.get("handoff") or {})
    try:
        from src.intent_agency_organ import build_intent_agency_status
        from src.operator_decision_ledger import (
            OperatorDecisionCheckpointError,
            _blast_radius_from_handoff,
            _drift_context_from_pipeline,
            append_checkpoint_block_event,
            evaluate_checkpoint_policy,
        )

        intent_status = build_intent_agency_status()
        policy = evaluate_checkpoint_policy(
            {
                "decision_kind": "otem_approval",
                "decision": "approve",
                "agency_claim_posture": intent_status.get("agency_claim_posture"),
                "blast_radius": _blast_radius_from_handoff(handoff),
                "drift_context": _drift_context_from_pipeline({}),
            }
        )
        if policy.get("action") in {"block", "defer"}:
            block_row = append_checkpoint_block_event(
                session_id,
                reason=str(policy.get("reason") or "checkpoint policy blocked OTEM approval"),
                drift_context=dict(policy.get("drift_context") or {}),
                approval_id=str(approval["id"]),
            )
            raise OperatorDecisionCheckpointError(
                str(policy.get("reason") or "checkpoint policy blocked OTEM approval"),
                decision_id=(block_row or {}).get("decision_id"),
                action=str(policy.get("action") or "block"),
            )
    except OperatorDecisionCheckpointError:
        raise
    except Exception:
        pass

    substrate = get_otem_execution_substrate()
    approved = substrate.approve(
        otem_execution_workflow_id,
        runtime_context="operator_runtime",
    )
    applied = substrate.apply(
        otem_execution_workflow_id,
        runtime_context="operator_runtime",
    )

    update_workflow_approval(approval["id"], "approved")
    output = dict(run_record.get("output") or {})
    exec_details = applied.get("apply_result") or applied
    output.update(
        {
            "message": "OTEM execution approved and applied through governed substrate.",
            "completedAt": now_iso(),
            "otem_execution_workflow_id": otem_execution_workflow_id,
            "substrate_approved": approved,
            "substrate_applied": applied,
            "substrate_stage": applied.get("stage"),
            # New observable plumbing: contractor execution results when live services were used
            "contractors_reachable": exec_details.get("contractors_reachable"),
            "execution_results": exec_details.get("execution_results"),
            "execution_note": exec_details.get("message"),
        }
    )
    update_workflow_run(workflow_run_id, status="completed", output=output)
    try:
        from src.operator_decision_ledger import append_otem_approval_event

        append_otem_approval_event(
            session_id,
            approval_id=str(approval["id"]),
            decision="approve",
            handoff=handoff,
            governed_pipeline={"execution_results": exec_details.get("execution_results"), "contractors": exec_details.get("contractors_reachable")},
        )
    except Exception:
        pass

    # Feed execution results back to the original OTEM session for end-to-end observability in chat/state
    try:
        from src.conversation_memory import conversation_memory
        session = conversation_memory.get_session(session_id)
        if session:
            exec_info = {
                "approval_id": str(approval["id"]),
                "otem_execution_workflow_id": otem_execution_workflow_id,
                "contractors_reachable": exec_details.get("contractors_reachable"),
                "execution_results": exec_details.get("execution_results"),
                "completed_at": now_iso(),
                "substrate_stage": applied.get("stage"),
            }
            session.metadata["last_otem_execution"] = exec_info
            # Merge into otem_state so it appears in the original OTEM chat trace / state / responses
            current_otem = dict(session.metadata.get("otem_state") or {})
            current_otem["last_execution"] = exec_info
            session.metadata["otem_state"] = current_otem
            # Append to response_trace for visibility in main Jarvis responses and traces
            try:
                from src.api import _append_response_trace_step
                response_trace = session.metadata.get("response_trace")
                if isinstance(response_trace, dict):
                    _append_response_trace_step(
                        response_trace,
                        f"OTEM execution completed: contractors_reachable={exec_info.get('contractors_reachable')}"
                    )
                    for er in exec_info.get("execution_results", []):
                        _append_response_trace_step(
                            response_trace,
                            f"  {er.get('label', er.get('step_id', 'step'))}: via={er.get('via', 'unknown')} {er.get('result_summary', er.get('note', ''))[:100]}"
                        )
            except Exception:
                pass
            # Record as session event if possible (for traces)
            try:
                from src.api import _record_session_event
                _record_session_event(
                    session,
                    "otem_execution_completed",
                    "OTEM handoff executed with contractors (or simulation).",
                    payload=exec_info,
                )
            except Exception:
                pass
    except Exception:
        pass

    return {
        "ok": True,
        "status": "approved",
        "substrate": applied,
    }


def is_otem_execution_approval(approval: dict[str, Any] | None) -> bool:
    return str((approval or {}).get("step_type") or "") == OTEM_EXECUTION_STEP_TYPE
