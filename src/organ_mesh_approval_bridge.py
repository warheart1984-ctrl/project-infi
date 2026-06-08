"""Bridge brain organ-mesh proposals into workflow approvals (Stage 4)."""

# Mythic: Organ Mesh Approval Bridge
# Engineering: OrganMeshApprovalBridgeEngine
from __future__ import annotations

import json
from typing import Any

from app.db import create_workflow_approval, create_workflow_run, get_workflow, now_iso
from app.db import get_conn
from app.workflow_validation import build_workflow_config_from_graph
from src.cisiv import normalize_cisiv_stage

ORGAN_MESH_SHELL_WORKFLOW_ID = "organ-mesh-run"
ORGAN_MESH_STEP_ID = "organ-mesh-approval"
ORGAN_MESH_STEP_TYPE = "organ_mesh_run"
ORGAN_MESH_STEP_LABEL = "Organ mesh run approval"


def _shell_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {"label": "Mesh Trigger", "kind": "trigger", "subtype": "manual", "config": {}},
        },
        {
            "id": ORGAN_MESH_STEP_ID,
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": ORGAN_MESH_STEP_LABEL,
                "kind": "action",
                "subtype": "task.create",
                "config": {},
            },
        },
    ]
    edges = [{"id": "edge-1", "source": "trigger-1", "target": ORGAN_MESH_STEP_ID}]
    return nodes, edges


def ensure_organ_mesh_shell_workflow() -> dict[str, Any]:
    existing = get_workflow(ORGAN_MESH_SHELL_WORKFLOW_ID)
    if existing:
        return existing
    nodes, edges = _shell_graph()
    config = build_workflow_config_from_graph("Organ Mesh Run", nodes, edges)
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
                ORGAN_MESH_SHELL_WORKFLOW_ID,
                "Organ Mesh Run",
                1,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                cisiv_stage,
                ts,
                ts,
            ),
        )
    workflow = get_workflow(ORGAN_MESH_SHELL_WORKFLOW_ID)
    if workflow is None:
        raise RuntimeError("Failed to create organ mesh shell workflow")
    return workflow


def _find_pending_mesh_approval(session_id: str, plan_id: str | None) -> dict[str, Any] | None:
    from app.db import list_pending_workflow_approvals

    for approval in list_pending_workflow_approvals(limit=200):
        if str(approval.get("step_type") or "") != ORGAN_MESH_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        if str(payload.get("brain_session_id") or "") != session_id:
            continue
        if plan_id and str(payload.get("plan_id") or "") != plan_id:
            continue
        return approval
    return None


def maybe_enqueue_organ_mesh_approval(
    session_id: str,
    mesh_plan: dict[str, Any],
    *,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Enqueue mesh run approval on brain accept — does not auto-execute."""
    normalized_session = str(session_id or "").strip()
    plan = dict(mesh_plan or {})
    if not normalized_session or plan.get("outcome") != "planned":
        return None

    plan_id = str(plan.get("plan_id") or "")
    existing = _find_pending_mesh_approval(normalized_session, plan_id or None)
    if existing:
        return {
            "approval_id": existing["id"],
            "workflow_run_id": existing["workflow_run_id"],
            "status": "pending",
            "deduped": True,
        }

    ensure_organ_mesh_shell_workflow()
    run_output = {
        "workflowName": "Organ Mesh Run",
        "trigger": {"type": "manual", "label": "Brain mesh proposal"},
        "totalSteps": 1,
        "currentStep": 1,
        "currentStepLabel": ORGAN_MESH_STEP_LABEL,
        "plannedSteps": [
            {
                "stepId": ORGAN_MESH_STEP_ID,
                "label": "Governed organ mesh run",
                "type": ORGAN_MESH_STEP_TYPE,
                "order": 1,
                "status": "awaiting_approval",
            }
        ],
        "message": "Paused for organ mesh operator approval.",
    }
    run_record = create_workflow_run(
        ORGAN_MESH_SHELL_WORKFLOW_ID,
        "awaiting_approval",
        run_output,
    )
    payload = {
        "brain_session_id": normalized_session,
        "plan_id": plan_id,
        "mesh_plan": plan,
        "proposal_snapshot": dict(proposal or {}),
        "occ_class": plan.get("occ_class") or "OCC-0",
        "cisiv_stage": "implementation",
    }
    approval = create_workflow_approval(
        run_record["id"],
        ORGAN_MESH_SHELL_WORKFLOW_ID,
        ORGAN_MESH_STEP_ID,
        ORGAN_MESH_STEP_LABEL,
        ORGAN_MESH_STEP_TYPE,
        "Brain accept enqueued organ mesh run proposal",
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
