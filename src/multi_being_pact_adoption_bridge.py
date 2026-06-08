"""Bridge brain multi-being pact candidates into workflow approvals (Stage 10)."""

# Mythic: Multi-Being Pact Adoption Bridge
# Engineering: MultiBeingPactAdoptionBridgeEngine
from __future__ import annotations

import json
from typing import Any

from app.db import create_workflow_approval, create_workflow_run, get_workflow, now_iso
from app.db import get_conn
from app.workflow_validation import build_workflow_config_from_graph
from src.cisiv import normalize_cisiv_stage

MULTI_BEING_SHELL_WORKFLOW_ID = "multi-being-pact-adoption"
MULTI_BEING_STEP_ID = "multi-being-pact-approval"
MULTI_BEING_STEP_TYPE = "multi_being_pact_adoption"
MULTI_BEING_STEP_LABEL = "Multi-being pact adoption approval"


def _shell_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {"label": "Multi-Being Trigger", "kind": "trigger", "subtype": "manual", "config": {}},
        },
        {
            "id": MULTI_BEING_STEP_ID,
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": MULTI_BEING_STEP_LABEL,
                "kind": "action",
                "subtype": "task.create",
                "config": {},
            },
        },
    ]
    edges = [{"id": "edge-1", "source": "trigger-1", "target": MULTI_BEING_STEP_ID}]
    return nodes, edges


def ensure_multi_being_shell_workflow() -> dict[str, Any]:
    existing = get_workflow(MULTI_BEING_SHELL_WORKFLOW_ID)
    if existing:
        return existing
    nodes, edges = _shell_graph()
    config = build_workflow_config_from_graph("Multi-Being Pact Adoption", nodes, edges)
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
                MULTI_BEING_SHELL_WORKFLOW_ID,
                "Multi-Being Pact Adoption",
                1,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                cisiv_stage,
                ts,
                ts,
            ),
        )
    workflow = get_workflow(MULTI_BEING_SHELL_WORKFLOW_ID)
    if workflow is None:
        raise RuntimeError("Failed to create multi-being shell workflow")
    return workflow


def _find_pending_multi_being_approval(session_id: str, candidate_id: str | None) -> dict[str, Any] | None:
    from app.db import list_pending_workflow_approvals

    for approval in list_pending_workflow_approvals(limit=200):
        if str(approval.get("step_type") or "") != MULTI_BEING_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        if str(payload.get("brain_session_id") or "") != session_id:
            continue
        if candidate_id and str(payload.get("candidate_id") or "") != candidate_id:
            continue
        return approval
    return None


def maybe_enqueue_multi_being_pact_adoption_approval(
    session_id: str,
    candidate: dict[str, Any],
    *,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Enqueue multi-being pact adoption on brain accept — does not auto-adopt."""
    normalized_session = str(session_id or "").strip()
    if not normalized_session or not candidate:
        return None

    candidate_id = str(candidate.get("candidate_id") or "")
    existing = _find_pending_multi_being_approval(normalized_session, candidate_id or None)
    if existing:
        return {
            "approval_id": existing["id"],
            "workflow_run_id": existing["workflow_run_id"],
            "status": "pending",
            "deduped": True,
        }

    ensure_multi_being_shell_workflow()
    run_output = {
        "workflowName": "Multi-Being Pact Adoption",
        "trigger": {"type": "manual", "label": "Brain multi-being pact candidate"},
        "totalSteps": 1,
        "currentStep": 1,
        "currentStepLabel": MULTI_BEING_STEP_LABEL,
        "plannedSteps": [
            {
                "stepId": MULTI_BEING_STEP_ID,
                "label": "Governed multi-being pact adoption",
                "type": MULTI_BEING_STEP_TYPE,
                "order": 1,
                "status": "awaiting_approval",
            }
        ],
        "message": "Paused for multi-being pact operator approval.",
    }
    run_record = create_workflow_run(
        MULTI_BEING_SHELL_WORKFLOW_ID,
        "awaiting_approval",
        run_output,
    )
    payload = {
        "brain_session_id": normalized_session,
        "candidate_id": candidate_id,
        "multi_being_candidate": candidate,
        "proposal_snapshot": dict(proposal or {}),
        "mbc_class": "MBC-1",
        "cisiv_stage": "implementation",
    }
    approval = create_workflow_approval(
        run_record["id"],
        MULTI_BEING_SHELL_WORKFLOW_ID,
        MULTI_BEING_STEP_ID,
        MULTI_BEING_STEP_LABEL,
        MULTI_BEING_STEP_TYPE,
        "Brain accept enqueued multi-being pact adoption proposal",
        payload,
    )
    if not approval:
        return None
    return {
        "approval_id": approval["id"],
        "workflow_run_id": run_record["id"],
        "status": "pending",
        "deduped": False,
    }
