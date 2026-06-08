"""Bridge brain habit candidates into workflow approvals (Stage 5)."""

# Mythic: Habit Adoption Bridge
# Engineering: HabitAdoptionBridgeEngine
from __future__ import annotations

import json
from typing import Any

from app.db import create_workflow_approval, create_workflow_run, get_workflow, now_iso
from app.db import get_conn
from app.workflow_validation import build_workflow_config_from_graph
from src.cisiv import normalize_cisiv_stage

HABIT_ADOPTION_SHELL_WORKFLOW_ID = "habit-adoption"
HABIT_ADOPTION_STEP_ID = "habit-adoption-approval"
HABIT_ADOPTION_STEP_TYPE = "habit_adoption"
HABIT_ADOPTION_STEP_LABEL = "Habit adoption approval"


def _shell_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [
        {
            "id": "trigger-1",
            "type": "triggerNode",
            "position": {"x": 40, "y": 220},
            "data": {"label": "Habit Trigger", "kind": "trigger", "subtype": "manual", "config": {}},
        },
        {
            "id": HABIT_ADOPTION_STEP_ID,
            "type": "actionNode",
            "position": {"x": 360, "y": 140},
            "data": {
                "label": HABIT_ADOPTION_STEP_LABEL,
                "kind": "action",
                "subtype": "task.create",
                "config": {},
            },
        },
    ]
    edges = [{"id": "edge-1", "source": "trigger-1", "target": HABIT_ADOPTION_STEP_ID}]
    return nodes, edges


def ensure_habit_adoption_shell_workflow() -> dict[str, Any]:
    existing = get_workflow(HABIT_ADOPTION_SHELL_WORKFLOW_ID)
    if existing:
        return existing
    nodes, edges = _shell_graph()
    config = build_workflow_config_from_graph("Habit Adoption", nodes, edges)
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
                HABIT_ADOPTION_SHELL_WORKFLOW_ID,
                "Habit Adoption",
                1,
                json.dumps(nodes),
                json.dumps(edges),
                json.dumps(config),
                cisiv_stage,
                ts,
                ts,
            ),
        )
    workflow = get_workflow(HABIT_ADOPTION_SHELL_WORKFLOW_ID)
    if workflow is None:
        raise RuntimeError("Failed to create habit adoption shell workflow")
    return workflow


def _find_pending_habit_approval(session_id: str, candidate_id: str | None) -> dict[str, Any] | None:
    from app.db import list_pending_workflow_approvals

    for approval in list_pending_workflow_approvals(limit=200):
        if str(approval.get("step_type") or "") != HABIT_ADOPTION_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        if str(payload.get("brain_session_id") or "") != session_id:
            continue
        if candidate_id and str(payload.get("candidate_id") or "") != candidate_id:
            continue
        return approval
    return None


def maybe_enqueue_habit_adoption_approval(
    session_id: str,
    candidate: dict[str, Any],
    *,
    proposal: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Enqueue habit adoption on brain accept — does not auto-adopt."""
    normalized_session = str(session_id or "").strip()
    if not normalized_session or not candidate:
        return None

    candidate_id = str(candidate.get("candidate_id") or candidate.get("pattern_key") or "")
    existing = _find_pending_habit_approval(normalized_session, candidate_id or None)
    if existing:
        return {
            "approval_id": existing["id"],
            "workflow_run_id": existing["workflow_run_id"],
            "status": "pending",
            "deduped": True,
        }

    ensure_habit_adoption_shell_workflow()
    run_output = {
        "workflowName": "Habit Adoption",
        "trigger": {"type": "manual", "label": "Brain habit candidate"},
        "totalSteps": 1,
        "currentStep": 1,
        "currentStepLabel": HABIT_ADOPTION_STEP_LABEL,
        "plannedSteps": [
            {
                "stepId": HABIT_ADOPTION_STEP_ID,
                "label": "Governed habit adoption",
                "type": HABIT_ADOPTION_STEP_TYPE,
                "order": 1,
                "status": "awaiting_approval",
            }
        ],
        "message": "Paused for habit adoption operator approval.",
    }
    run_record = create_workflow_run(
        HABIT_ADOPTION_SHELL_WORKFLOW_ID,
        "awaiting_approval",
        run_output,
    )
    payload = {
        "brain_session_id": normalized_session,
        "candidate_id": candidate_id,
        "habit_candidate": candidate,
        "proposal_snapshot": dict(proposal or {}),
        "hcc_class": "HCC-1",
        "cisiv_stage": "implementation",
    }
    approval = create_workflow_approval(
        run_record["id"],
        HABIT_ADOPTION_SHELL_WORKFLOW_ID,
        HABIT_ADOPTION_STEP_ID,
        HABIT_ADOPTION_STEP_LABEL,
        HABIT_ADOPTION_STEP_TYPE,
        "Brain accept enqueued habit adoption proposal",
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
