"""Constitutional lifecycle helpers for operator tasks (Article XV vertical slice)."""

from __future__ import annotations

from typing import Any

from constitutional.runtime import (
    ConstitutionalStateRuntime,
    StateObject,
    TransitionPayloadV2,
    TransitionReceiptV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
    utc_now_rfc3339,
)
from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
)

from operator_kernel.receipts_store import append_receipt

ACCOUNTABLE_PARTY = "operator"
RUNTIME_NAME = "OperatorRuntime"


def register_operator_task(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    *,
    goal: str,
) -> StateObject:
    """Register a new operator_task StateObject at Proposed."""
    state = StateObject(
        state_id=task_id,
        state_type="operator_task",
        current_state="Proposed",
        invariants=["operator_task_must_be_governed"],
        evidence_requirements=["task_request_payload"],
        authority_model=["operator", "runtime_law_spine"],
        reproducibility_requirements=["same_input_same_plan"],
        impact_boundaries=["local_repo", "configured_tools"],
        accountability_chain=["operator", "aais_runtime"],
    )
    csr.register_state(state)
    return state


def _last_lineage_hash(csr: ConstitutionalStateRuntime, task_id: str) -> str | None:
    receipts = csr.receipts_for(task_id)
    if not receipts:
        return None
    return receipts[-1].continuity.lineage_hash


def _last_receipt_id(csr: ConstitutionalStateRuntime, task_id: str) -> str | None:
    receipts = csr.receipts_for(task_id)
    if not receipts:
        return None
    return receipts[-1].receipt_id


def build_operator_transition_receipt(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    *,
    from_state: str,
    to_state: str,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> TransitionReceiptV2:
    rid = new_receipt_id("op-transition")
    payload_hash = stable_json_hash(payload or {"kind": kind})
    prev_id = _last_receipt_id(csr, task_id)
    prev_lineage = _last_lineage_hash(csr, task_id)
    lineage = compute_lineage_hash(
        previous_receipt_id=prev_id,
        receipt_id=rid,
        payload_hash=payload_hash,
        previous_lineage_hash=prev_lineage,
    )
    return TransitionReceiptV2(
        receipt_id=rid,
        runtime=RUNTIME_NAME,
        timestamp=utc_now_rfc3339(),
        action_type="state_transition",
        inputs=ReceiptInputsV2(
            request_id=task_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=task_id),
        ),
        outputs=ReceiptOutputsV2(status=kind.lower(), result_hash=payload_hash),
        invariant=InvariantBlockV2(
            name="operator_task_must_follow_governed_lifecycle",
            description="Operator task transitions follow Article XV graph",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"evb-{task_id}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="operator_kernel",
            jurisdiction="local_operator_scope",
            legitimacy_basis="runtime_law_spine",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["local_repo", "configured_tools"],
            scope_out=["external_unconfigured"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party=ACCOUNTABLE_PARTY),
        signatures=SignaturesBlockV2(runtime_signature=f"{RUNTIME_NAME}:v0"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=prev_id,
            thread_id=task_id,
            lineage_hash=lineage,
        ),
        lifecycle=LifecycleBlockV2(stage="decision"),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis=legal_basis,
            receipt_ids_used=[prev_id] if prev_id else [],
            state_id=task_id,
            state_type="operator_task",
        ),
    )


def emit_operator_transition(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    *,
    to_state: str,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> TransitionReceiptV2:
    """Emit Receipt v2 and apply a legal constitutional transition."""
    state = csr.get_state(task_id)
    receipt = build_operator_transition_receipt(
        csr,
        task_id,
        from_state=state.current_state,
        to_state=to_state,
        kind=kind,
        legal_basis=legal_basis,
        payload=payload,
    )
    csr.apply_transition(task_id, receipt, accountable_party=ACCOUNTABLE_PARTY)
    append_receipt(receipt)
    return receipt


def advance_operator_happy_path(
    csr: ConstitutionalStateRuntime,
    task_id: str,
    *,
    target: str,
    kind: str,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Walk legal edges until target state (happy-path slice)."""
    path_edges: dict[str, list[str]] = {
        "Evaluated": ["Proposed", "Evaluated"],
        "Approved": ["Proposed", "Evaluated", "Approved"],
        "Executed": ["Proposed", "Evaluated", "Approved", "Executed"],
        "Observed": ["Proposed", "Evaluated", "Approved", "Executed", "Observed"],
        "Closed": ["Proposed", "Evaluated", "Approved", "Executed", "Observed", "Closed"],
    }
    sequence = path_edges.get(target)
    if sequence is None:
        raise ValueError(f"unsupported constitutional target: {target}")

    emitted: list[TransitionReceiptV2] = []
    for idx in range(1, len(sequence)):
        from_s, to_s = sequence[idx - 1], sequence[idx]
        current = csr.get_state(task_id).current_state
        if current == to_s:
            continue
        if current != from_s:
            # Re-sync by walking from current toward target
            break
        emitted.append(
            emit_operator_transition(
                csr,
                task_id,
                to_state=to_s,
                kind=kind if to_s == target else "Decision",
                legal_basis=legal_basis if to_s == target else f"advance:{from_s}->{to_s}",
                payload=payload if to_s == target else None,
            )
        )
    # If we broke early, continue stepping until target or stuck
    while csr.get_state(task_id).current_state != target:
        current = csr.get_state(task_id).current_state
        next_map = {
            "Proposed": "Evaluated",
            "Evaluated": "Approved",
            "Approved": "Executed",
            "Executed": "Observed",
            "Observed": "Closed",
        }
        nxt = next_map.get(current)
        if nxt is None:
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


def sync_meta_constitutional(meta: dict[str, Any], csr: ConstitutionalStateRuntime, task_id: str) -> None:
    try:
        meta["constitutional_state"] = csr.get_state(task_id).current_state
    except KeyError:
        pass
