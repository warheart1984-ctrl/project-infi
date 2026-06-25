"""Startup reconciliation for OTEM substrate vs pending workflow approvals."""

# Mythic: Otem Substrate Reconciler
# Engineering: OtemSubstrateReconcilerEngine
from __future__ import annotations

from typing import Any

from app.db import (
    get_workflow_run,
    list_pending_workflow_approvals,
    mark_workflow_approval_stale,
    mark_workflow_run_stale,
    now_iso,
    update_workflow_run,
)
from src.otem_execution_approval_bridge import OTEM_EXECUTION_STEP_TYPE
from src.otem.store import (
    load_substrate_workflow,
    rehydrate_substrate_workflow_from_proposal,
    substrate_db_enabled,
)


def reconcile_otem_substrate_on_startup() -> dict[str, Any]:
    """Reconcile pending OTEM approvals with durable substrate; fail-closed on orphans."""
    if not substrate_db_enabled():
        return {"reconciled": False, "reason": "substrate_db_disabled", "stale_count": 0}

    from src.otem.execution import get_otem_execution_substrate

    substrate = get_otem_execution_substrate()
    stale_count = 0
    rehydrated_count = 0
    loaded_count = 0

    for row in load_substrate_workflow_from_db_batch():
        workflow_id = str(row.get("workflow_id") or "")
        if workflow_id and workflow_id not in substrate._workflows:
            from src.otem.execution import OTEMExecutionWorkflow

            substrate._workflows[workflow_id] = OTEMExecutionWorkflow(
                workflow_id=workflow_id,
                stage=str(row.get("stage") or "proposal"),
                proposal=dict(row.get("proposal") or {}),
                operator_approved=bool(row.get("operator_approved")),
                preview=dict(row.get("preview") or {}) if row.get("preview") else None,
                apply_result=dict(row.get("apply_result") or {}) if row.get("apply_result") else None,
                created_at=str(row.get("created_at") or now_iso()),
                updated_at=str(row.get("updated_at") or now_iso()),
            )
            loaded_count += 1

    for approval in list_pending_workflow_approvals(limit=500):
        if str(approval.get("step_type") or "") != OTEM_EXECUTION_STEP_TYPE:
            continue
        payload = dict(approval.get("payload") or {})
        workflow_id = str(payload.get("otem_execution_workflow_id") or "").strip()
        if not workflow_id:
            mark_stale_approval_and_run(approval, "missing otem_execution_workflow_id")
            stale_count += 1
            continue

        if workflow_id in substrate._workflows:
            continue

        durable = load_substrate_workflow(workflow_id)
        if durable:
            rehydrate_substrate_workflow_from_proposal(
                workflow_id,
                dict(durable.get("proposal") or {}),
                stage=str(durable.get("stage") or "proposal"),
            )
            rehydrated_count += 1
            continue

        proposal_snapshot = dict(payload.get("proposal_snapshot") or {})
        if proposal_snapshot:
            rehydrate_substrate_workflow_from_proposal(workflow_id, proposal_snapshot)
            rehydrated_count += 1
            continue

        mark_stale_approval_and_run(
            approval,
            "substrate workflow missing after restart; reject and re-run OTEM handoff",
        )
        stale_count += 1

    summary = {
        "reconciled": True,
        "loaded_count": loaded_count,
        "rehydrated_count": rehydrated_count,
        "stale_count": stale_count,
    }
    if stale_count or rehydrated_count or loaded_count:
        try:
            from src.operator_decision_ledger import append_substrate_reconcile_event

            append_substrate_reconcile_event(summary)
        except Exception:
            pass
    return summary


def load_substrate_workflow_from_db_batch() -> list[dict[str, Any]]:
    from src.otem.store import load_all_substrate_workflows

    return load_all_substrate_workflows()


def mark_stale_approval_and_run(approval: dict[str, Any], reason: str) -> None:
    approval_id = str(approval.get("id") or "")
    run_id = str(approval.get("workflow_run_id") or "")
    mark_workflow_approval_stale(approval_id, reason)
    run_record = get_workflow_run(run_id) or {}
    if run_record.get("status") == "awaiting_approval":
        output = dict(run_record.get("output") or {})
        output.update(
            {
                "message": reason,
                "staleAt": now_iso(),
                "substrate_reconcile_status": "stale",
            }
        )
        update_workflow_run(run_id, status="stale", output=output)
    elif run_record.get("status") == "running":
        mark_workflow_run_stale(run_id, reason, now_iso())
