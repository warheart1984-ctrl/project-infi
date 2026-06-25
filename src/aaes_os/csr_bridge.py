"""Constitutional State Runtime bridge for AAIS cognitive spans."""

from __future__ import annotations

from typing import Any

from constitutional.runtime import (
    ConstitutionalStateRuntime,
    StateObject,
    TransitionReceiptV2,
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
    TransitionPayloadV2,
    compute_lineage_hash,
)

from src.aaes_os.types import SpanState

ACCOUNTABLE_PARTY = "aais-runtime"
RUNTIME_NAME = "AAIS.CognitiveSpanRuntime"
SPAN_STATE_TYPE = "cognitive_span"

SPAN_STATE_TO_CONSTITUTIONAL: dict[str, str] = {
    SpanState.INIT.value: "Proposed",
    SpanState.INTENTED.value: "Evaluated",
    SpanState.DECIDED.value: "Approved",
    SpanState.EXECUTING.value: "Executed",
    SpanState.RESULTED.value: "Observed",
    SpanState.CLOSED.value: "Closed",
}

_CONSTITUTIONAL_ORDER: list[str] = [
    "Proposed",
    "Evaluated",
    "Approved",
    "Executed",
    "Observed",
    "Closed",
]

_FORWARD_EDGE: dict[str, str] = {
    "Proposed": "Evaluated",
    "Evaluated": "Approved",
    "Approved": "Executed",
    "Executed": "Observed",
    "Observed": "Closed",
}


def _aais_persist_root():
    import os
    from pathlib import Path

    runtime_dir = os.getenv("AAIS_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "constitutional" / "aais"
    return Path(".runtime") / "constitutional" / "aais"


def get_aais_csr() -> ConstitutionalStateRuntime:
    from constitutional.runtime import ConstitutionalStateRuntime

    if not hasattr(get_aais_csr, "_instance"):
        get_aais_csr._instance = ConstitutionalStateRuntime(persist_root=_aais_persist_root())  # type: ignore[attr-defined]
    return get_aais_csr._instance  # type: ignore[attr-defined]


def register_cognitive_span(
    csr: ConstitutionalStateRuntime,
    span_id: str,
    *,
    trace_id: str | None = None,
) -> StateObject:
    state = StateObject(
        state_id=span_id,
        state_type=SPAN_STATE_TYPE,
        current_state="Proposed",
        invariants=["span_traceability", "span_causality", "span_identity"],
        evidence_requirements=["trace_event_chain"],
        authority_model=["aais-runtime", "policy-engine"],
        reproducibility_requirements=["trace_replay"],
        impact_boundaries=["governed_module_scope"],
        accountability_chain=[ACCOUNTABLE_PARTY],
    )
    csr.register_state(state)
    if trace_id:
        apply_span_transition(
            csr,
            span_id,
            to_state="Evaluated",
            kind="Decision",
            legal_basis="span_registered",
            payload={"trace_id": trace_id},
        )
    return state


def _last_receipt_id(csr: ConstitutionalStateRuntime, span_id: str) -> str | None:
    receipts = csr.receipts_for(span_id)
    return receipts[-1].receipt_id if receipts else None


def _last_lineage_hash(csr: ConstitutionalStateRuntime, span_id: str) -> str | None:
    receipts = csr.receipts_for(span_id)
    return receipts[-1].continuity.lineage_hash if receipts else None


def apply_span_transition(
    csr: ConstitutionalStateRuntime,
    span_id: str,
    *,
    to_state: str,
    kind: str,
    legal_basis: str,
    receipt_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> TransitionReceiptV2:
    state = csr.get_state(span_id)
    rid = receipt_id or new_receipt_id("aais-span")
    payload_hash = stable_json_hash(payload or {"kind": kind, "span_id": span_id})
    prev_id = _last_receipt_id(csr, span_id)
    prev_lineage = _last_lineage_hash(csr, span_id)
    lineage = compute_lineage_hash(
        previous_receipt_id=prev_id,
        receipt_id=rid,
        payload_hash=payload_hash,
        previous_lineage_hash=prev_lineage,
    )
    receipt = TransitionReceiptV2(
        receipt_id=rid,
        runtime=RUNTIME_NAME,
        timestamp=utc_now_rfc3339(),
        action_type="state_transition",
        inputs=ReceiptInputsV2(
            request_id=span_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=span_id),
        ),
        outputs=ReceiptOutputsV2(status=kind.lower(), result_hash=payload_hash),
        invariant=InvariantBlockV2(
            name="cognitive_span_must_follow_governed_lifecycle",
            description="AAIS span transitions follow Article XV graph",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"evb-span-{span_id}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="aaes_os",
            jurisdiction="cognitive_span_scope",
            legitimacy_basis="governed_span_engine",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["governed_module_scope"],
            scope_out=["ungoverned_execution"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party=ACCOUNTABLE_PARTY),
        signatures=SignaturesBlockV2(runtime_signature=f"{RUNTIME_NAME}:v0"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=prev_id,
            thread_id=span_id,
            lineage_hash=lineage,
        ),
        lifecycle=LifecycleBlockV2(stage=kind.lower()),
        transition=TransitionPayloadV2(
            from_state=state.current_state,
            to_state=to_state,
            legal_basis=legal_basis,
            receipt_ids_used=[prev_id] if prev_id else [],
            state_id=span_id,
            state_type=SPAN_STATE_TYPE,
        ),
    )
    csr.apply_transition(span_id, receipt, accountable_party=ACCOUNTABLE_PARTY)
    return receipt


def _rank(state: str) -> int:
    try:
        return _CONSTITUTIONAL_ORDER.index(state)
    except ValueError:
        return -1


def sync_span_state_to_csr(
    csr: ConstitutionalStateRuntime,
    span_id: str,
    span_state: SpanState,
    *,
    receipt_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Map SpanState enum to constitutional graph and advance CSR."""
    target = SPAN_STATE_TO_CONSTITUTIONAL.get(span_state.value, "Proposed")
    try:
        csr.get_state(span_id)
    except KeyError:
        register_cognitive_span(csr, span_id)

    emitted: list[TransitionReceiptV2] = []
    while csr.get_state(span_id).current_state != target:
        current = csr.get_state(span_id).current_state
        if _rank(target) < _rank(current):
            break
        nxt = _FORWARD_EDGE.get(current)
        if nxt is None or _rank(nxt) > _rank(target):
            break
        emitted.append(
            apply_span_transition(
                csr,
                span_id,
                to_state=nxt,
                kind="Observation" if nxt in {"Executed", "Observed"} else "Decision",
                legal_basis=f"span_state:{span_state.value}",
                receipt_id=receipt_id if nxt == target else None,
                payload=payload if nxt == target else None,
            )
        )
        if nxt == target:
            break
    return emitted
