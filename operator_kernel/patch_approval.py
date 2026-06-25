"""Approve or reject pending write_patch previews (interim Coding Organs gate)."""

from __future__ import annotations

from pathlib import Path

from operator_kernel.config import OperatorKernelConfig
from operator_kernel.contracts import PatchApprovalResponse, TaskConstraints
from operator_kernel.events import TaskEventStore
from operator_kernel.governance_gate import GovernanceGate
from operator_kernel.tools.patch import apply_unified_diff


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def approve_pending_patch(
    task_id: str,
    store: TaskEventStore,
    gate: GovernanceGate,
    config: OperatorKernelConfig,
) -> PatchApprovalResponse:
    meta = store.read_meta(task_id)
    if meta.get("status") != "awaiting_approval":
        return PatchApprovalResponse(
            task_id=task_id,
            status=str(meta.get("status", "unknown")),
            applied=False,
            message="task is not awaiting patch approval",
        )

    pending = meta.get("pending_patch") or {}
    path = str(pending.get("path") or "").strip()
    diff = str(pending.get("diff") or "")
    call_id = str(pending.get("id") or "")
    if not path or not diff:
        return PatchApprovalResponse(
            task_id=task_id,
            status="awaiting_approval",
            applied=False,
            message="no pending patch on task",
        )

    constraints = TaskConstraints(**(meta.get("constraints") or {}))
    verdict, receipt = gate.check_tool(
        "write_patch",
        {"path": path, "diff": diff},
        constraints,
        tool_call_id=call_id or None,
    )
    store.append(task_id, "law_receipt", receipt.model_dump())
    if verdict.verdict == "deny":
        err = verdict.reason or "governance denied patch apply"
        store.append(task_id, "error", {"message": err, "tool": "write_patch"})
        return PatchApprovalResponse(
            task_id=task_id,
            status="awaiting_approval",
            applied=False,
            path=path,
            message=err,
        )

    root = config.resolved_workspace_root()
    try:
        result = apply_unified_diff(root, path, diff)
    except Exception as exc:
        store.append(task_id, "error", {"message": str(exc), "tool": "write_patch"})
        return PatchApprovalResponse(
            task_id=task_id,
            status="awaiting_approval",
            applied=False,
            path=path,
            message=str(exc),
        )

    store.append(
        task_id,
        "patch_applied",
        {"id": call_id, "path": path, "result": result},
    )
    store.append(
        task_id,
        "tool_result",
        {
            "id": call_id,
            "name": "write_patch",
            "ok": True,
            "data": {**result, "applied_after_approval": True},
        },
    )

    meta.pop("pending_patch", None)
    meta["status"] = "completed"
    meta["updated_at"] = _utc_now()
    from operator_kernel.csr import CSR
    from operator_kernel.observer_packet import constitutional_close_task
    from operator_kernel.status_mapping import sync_operator_status_to_csr

    sync_operator_status_to_csr(CSR, task_id, meta, kind="Observation", legal_basis="patch_approved")
    constitutional_close_task(
        task_id,
        meta,
        kind="Closure",
        legal_basis="patch_applied",
        payload={"path": path},
    )
    store.write_meta(task_id, meta)
    store.append(
        task_id,
        "task_completed",
        {"summary": f"Patch applied to {path}", "status": "completed"},
    )

    return PatchApprovalResponse(
        task_id=task_id,
        status=str(meta.get("status", "closed")),
        applied=True,
        path=path,
        message="patch applied",
    )


def reject_pending_patch(
    task_id: str,
    store: TaskEventStore,
    reason: str = "",
) -> PatchApprovalResponse:
    meta = store.read_meta(task_id)
    if meta.get("status") != "awaiting_approval":
        return PatchApprovalResponse(
            task_id=task_id,
            status=str(meta.get("status", "unknown")),
            applied=False,
            message="task is not awaiting patch approval",
        )

    pending = meta.get("pending_patch") or {}
    path = str(pending.get("path") or "")
    call_id = str(pending.get("id") or "")
    msg = reason.strip() or "patch rejected by operator"

    store.append(
        task_id,
        "patch_rejected",
        {"id": call_id, "path": path, "reason": msg},
    )
    store.append(
        task_id,
        "tool_result",
        {
            "id": call_id,
            "name": "write_patch",
            "ok": False,
            "error": msg,
            "data": {"rejected": True, "path": path},
        },
    )

    meta.pop("pending_patch", None)
    meta["status"] = "cancelled"
    meta["updated_at"] = _utc_now()
    from operator_kernel.csr import CSR
    from operator_kernel.observer_packet import emit_observer_packet_if_closed
    from operator_kernel.status_mapping import sync_operator_status_to_csr

    sync_operator_status_to_csr(CSR, task_id, meta, kind="Closure", legal_basis="patch_rejected")
    packet = emit_observer_packet_if_closed(task_id, meta)
    if packet:
        meta["constitutional_observer_packet"] = str(packet)
    store.write_meta(task_id, meta)
    store.append(task_id, "task_completed", {"summary": msg, "status": "rejected"})

    return PatchApprovalResponse(
        task_id=task_id,
        status=str(meta.get("status", "cancelled")),
        applied=False,
        path=path,
        message=msg,
    )
