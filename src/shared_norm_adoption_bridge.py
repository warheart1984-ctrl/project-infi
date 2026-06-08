"""Bridge brain shared norm candidates into workflow approvals (Stage 11)."""

from __future__ import annotations

import json
from typing import Any

from app.db import create_workflow_approval, create_workflow_run, get_workflow, now_iso
from app.db import get_conn
from app.workflow_validation import build_workflow_config_from_graph
from src.cisiv import normalize_cisiv_stage

COB_SHELL_WORKFLOW_ID = "shared-norm-adoption"
COB_STEP_ID = "shared-norm-approval"
COB_STEP_TYPE = "shared_norm_adoption"
COB_STEP_LABEL = "Shared norm adoption approval"


def _shell_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {"label": "Culture-of-Beings Trigger", "kind": "trigger", "subtype": "manual", "config": {}},
        },
        {
            "id": COB_STEP_ID,
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {"label": COB_STEP_LABEL, "kind": "action", "subtype": "task.create", "config": {}},
        },
    ]
    edges = [{"id": "edge-1", "source": "trigger-1", "target": COB_STEP_ID}]
    return nodes, edges


def ensure_shared_norm_shell_workflow() -> dict[str, Any]:
    existing = get_workflow(COB_SHELL_WORKFLOW_ID)
    if existing:
        return existing
    nodes, edges = _shell_graph()
    config = build_workflow_config_from_graph("Shared Norm Adoption", nodes, edges)
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
                COB_SHELL_WORKFLOW_ID,
                "Shared Norm Adoption",
                1,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                cisiv_stage,
                ts,
                ts,
            ),
        )
    workflow = get_workflow(COB_SHELL_WORKFLOW_ID)
    if workflow is None:
        raise RuntimeError("Failed to create shared norm shell workflow")
    return workflow


def maybe_enqueue_shared_norm_adoption_approval(
    session_id: str,
    candidate: dict[str, Any],
    *,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Enqueue shared norm adoption on brain accept — does not auto-adopt."""
    normalized_session = str(session_id or "").strip()
    if not normalized_session or not candidate:
        return None

    candidate_id = str(candidate.get("candidate_id") or "")
    from app.db import list_pending_workflow_approvals

    for approval in list_pending_workflow_approvals(limit=200):
        if str(approval.get("step_type") or "") != COB_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        if str(payload.get("brain_session_id") or "") != normalized_session:
            continue
        if candidate_id and str(payload.get("candidate_id") or "") != candidate_id:
            continue
        return {
            "approval_id": approval["id"],
            "workflow_run_id": approval["workflow_run_id"],
            "status": "pending",
            "deduped": True,
        }

    ensure_shared_norm_shell_workflow()
    run_record = create_workflow_run(
        COB_SHELL_WORKFLOW_ID,
        "awaiting_approval",
        {"workflowName": "Shared Norm Adoption", "message": "Paused for operator approval."},
    )
    payload = {
        "brain_session_id": normalized_session,
        "candidate_id": candidate_id,
        "shared_norm_candidate": candidate,
        "proposal_snapshot": dict(proposal or {}),
        "cob_class": "COB-1",
    }
    approval = create_workflow_approval(
        run_record["id"],
        COB_SHELL_WORKFLOW_ID,
        COB_STEP_ID,
        COB_STEP_LABEL,
        COB_STEP_TYPE,
        "Brain accept enqueued shared norm adoption proposal",
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
