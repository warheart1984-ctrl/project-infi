"""Map operator meta[\"status\"] to the universal constitutional state graph."""

from __future__ import annotations

from typing import Any

from constitutional.runtime import ConstitutionalStateRuntime, TransitionReceiptV2

from operator_kernel.constitutional_task import (
    ACCOUNTABLE_PARTY,
    emit_operator_transition,
    sync_meta_constitutional,
)

# Operator meta["status"] → constitutional state (single source of truth)
OPERATOR_STATUS_TO_CONSTITUTIONAL: dict[str, str] = {
    # operator_kernel meta["status"] values (production)
    "queued": "Proposed",
    "planned": "Evaluated",
    "running": "Evaluated",
    "executing": "Executed",
    "awaiting_approval": "Approved",
    "completed": "Observed",
    "failed": "Observed",
    "cancelled": "Closed",
    # aliases / future operator phases
    "created": "Proposed",
    "approved": "Approved",
    "succeeded": "Observed",
    "closed": "Closed",
    "challenged": "Challenged",
    "remediating": "Remediated",
}

OPERATOR_STATUS_RECEIPT_KIND: dict[str, str] = {
    "queued": "Decision",
    "created": "Decision",
    "planned": "Decision",
    "running": "Observation",
    "executing": "Observation",
    "awaiting_approval": "Decision",
    "approved": "Decision",
    "completed": "Observation",
    "succeeded": "Observation",
    "failed": "Observation",
    "cancelled": "Closure",
    "closed": "Closure",
    "challenged": "Observation",
    "remediating": "Decision",
}

_CONSTITUTIONAL_ORDER: list[str] = [
    "Proposed",
    "Evaluated",
    "Approved",
    "Executed",
    "Observed",
    "Challenged",
    "Arbitrated",
    "Remediated",
    "Closed",
]

_FORWARD_EDGE: dict[str, str] = {
    "Proposed": "Evaluated",
    "Evaluated": "Approved",
    "Approved": "Executed",
    "Executed": "Observed",
    "Observed": "Closed",
    "Challenged": "Arbitrated",
    "Arbitrated": "Remediated",
    "Remediated": "Closed",
}


def constitutional_target_for_operator_status(operator_status: str) -> str:
    try:
        return OPERATOR_STATUS_TO_CONSTITUTIONAL[operator_status]
    except KeyError as exc:
        raise ValueError(f"unknown operator status: {operator_status}") from exc


def receipt_kind_for_operator_status(operator_status: str) -> str:
    return OPERATOR_STATUS_RECEIPT_KIND.get(operator_status, "Decision")


def _rank(state: str) -> int:
    try:
        return _CONSTITUTIONAL_ORDER.index(state)
    except ValueError:
        return -1


def advance_to_constitutional_state(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    target: str,
    *,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Walk legal forward edges until the state object reaches target."""
    emitted: list[TransitionReceiptV2] = []
    while csr.get_state(task_id).current_state != target:
        current = csr.get_state(task_id).current_state
        if _rank(target) < _rank(current):
            break
        nxt = _FORWARD_EDGE.get(current)
        if nxt is None:
            break
        if _rank(nxt) > _rank(target):
            break
        emitted.append(
            emit_operator_transition(
                csr,
                task_id,
                to_state=nxt,
                kind=kind if nxt == target else "Decision",
                legal_basis=legal_basis if nxt == target else f"advance:{current}->{nxt}",
                payload=payload if nxt == target else None,
            )
        )
        if nxt == target:
            break
    return emitted


def sync_operator_status_to_csr(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    meta: dict[str, Any],
    *,
    kind: str | None = None,
    legal_basis: str | None = None,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Derive constitutional state from meta[\"status\"] and advance CSR if needed."""
    operator_status = str(meta.get("status") or "queued")
    target = constitutional_target_for_operator_status(operator_status)
    resolved_kind = kind or receipt_kind_for_operator_status(operator_status)
    resolved_basis = legal_basis or f"operator_status:{operator_status}"
    receipts = advance_to_constitutional_state(
        csr,
        task_id,
        target,
        kind=resolved_kind,
        legal_basis=resolved_basis,
        payload=payload,
    )
    sync_meta_constitutional(meta, csr, task_id)
    return receipts
