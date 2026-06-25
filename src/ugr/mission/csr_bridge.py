"""Constitutional State Runtime bridge for URG missions (Article XV)."""

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
)

ACCOUNTABLE_PARTY = "urg-operator"
RUNTIME_NAME = "URG.MissionRuntime"
URG_MISSION_RUNTIME_ID = "aais.urg.mission_runtime"
MISSION_STATE_TYPE = "mission"

# URG mission response status → constitutional target state
URG_STATUS_TO_CONSTITUTIONAL: dict[str, str] = {
    "ok": "Closed",
    "blocked": "Closed",
    "rejected": "Closed",
    # in-flight labels (cloud manifold / internal)
    "open": "Evaluated",
    "active": "Executed",
    "step_append": "Executed",
}

URG_STATUS_RECEIPT_KIND: dict[str, str] = {
    "ok": "Closure",
    "blocked": "Remediation",
    "rejected": "Decision",
    "open": "Decision",
    "active": "Observation",
    "step_append": "Observation",
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

_BLOCKED_PATH: list[str] = ["Challenged", "Arbitrated", "Remediated", "Closed"]

_KIND_TO_LIFECYCLE_STAGE: dict[str, str] = {
    "Decision": "decision",
    "Observation": "observation",
    "Divergence": "divergence",
    "Arbitration": "remediation",
    "Remediation": "remediation",
    "Closure": "closure",
}


def register_mission_state(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    ingress: dict[str, Any] | None = None,
) -> StateObject:
    """Register a mission StateObject at Proposed after cloud invariants pass."""
    ingress = dict(ingress or {})
    state = StateObject(
        state_id=mission_id,
        state_type=MISSION_STATE_TYPE,
        current_state="Proposed",
        invariants=["cloud_invariant_set", "mission_continuity", "tenant_boundary"],
        evidence_requirements=["mission_ingress_stamp", "cloud_manifold"],
        authority_model=["urg-operator", "cloud_invariants"],
        reproducibility_requirements=["ledger_merkle_root", "mission_receipt"],
        impact_boundaries=[
            str(ingress.get("tenant_id") or "default"),
            str(ingress.get("boundary_digest") or "cloud_boundary"),
        ],
        accountability_chain=[
            str(ingress.get("operator_id") or ACCOUNTABLE_PARTY),
            RUNTIME_NAME,
        ],
    )
    csr.register_state(state)
    return state


def _last_lineage_hash(csr: ConstitutionalStateRuntime, mission_id: str) -> str | None:
    receipts = csr.receipts_for(mission_id)
    if not receipts:
        return None
    return receipts[-1].continuity.lineage_hash


def _last_receipt_id(csr: ConstitutionalStateRuntime, mission_id: str) -> str | None:
    receipts = csr.receipts_for(mission_id)
    if not receipts:
        return None
    return receipts[-1].receipt_id


def build_mission_transition_receipt(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    from_state: str,
    to_state: str,
    kind: str,
    legal_basis: str,
    receipt_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> TransitionReceiptV2:
    rid = receipt_id or new_receipt_id("urg-mission")
    payload_hash = stable_json_hash(payload or {"kind": kind, "mission_id": mission_id})
    prev_id = _last_receipt_id(csr, mission_id)
    prev_lineage = _last_lineage_hash(csr, mission_id)
    from constitutional.runtime.receipts_v2 import compute_lineage_hash

    lineage = compute_lineage_hash(
        previous_receipt_id=prev_id,
        receipt_id=rid,
        payload_hash=payload_hash,
        previous_lineage_hash=prev_lineage,
    )
    lifecycle_stage = _KIND_TO_LIFECYCLE_STAGE.get(kind, "decision")
    return TransitionReceiptV2(
        receipt_id=rid,
        runtime=RUNTIME_NAME,
        timestamp=utc_now_rfc3339(),
        action_type="state_transition",
        inputs=ReceiptInputsV2(
            request_id=mission_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=mission_id),
        ),
        outputs=ReceiptOutputsV2(status=kind.lower(), result_hash=payload_hash),
        invariant=InvariantBlockV2(
            name="mission_must_follow_cloud_invariants",
            description="URG mission transitions follow Article XV graph",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"evb-mission-{mission_id}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source=URG_MISSION_RUNTIME_ID,
            jurisdiction="urg_mission_scope",
            legitimacy_basis="cloud_invariant_set",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=["tenant_boundary", "cloud_manifold"],
            scope_out=["unauthorized_organ"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party=ACCOUNTABLE_PARTY),
        signatures=SignaturesBlockV2(runtime_signature=f"{RUNTIME_NAME}:v0"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=prev_id,
            thread_id=mission_id,
            lineage_hash=lineage,
        ),
        lifecycle=LifecycleBlockV2(stage=lifecycle_stage),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis=legal_basis,
            receipt_ids_used=[prev_id] if prev_id else [],
            state_id=mission_id,
            state_type=MISSION_STATE_TYPE,
        ),
    )


def apply_mission_transition(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    to_state: str,
    kind: str,
    legal_basis: str,
    receipt_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> TransitionReceiptV2:
    """Emit Receipt v2 and apply a legal constitutional transition for a mission."""
    state = csr.get_state(mission_id)
    receipt = build_mission_transition_receipt(
        csr,
        mission_id,
        from_state=state.current_state,
        to_state=to_state,
        kind=kind,
        legal_basis=legal_basis,
        receipt_id=receipt_id,
        payload=payload,
    )
    csr.apply_transition(mission_id, receipt, accountable_party=ACCOUNTABLE_PARTY)
    return receipt


def _rank(state: str) -> int:
    try:
        return _CONSTITUTIONAL_ORDER.index(state)
    except ValueError:
        return -1


def advance_mission_to(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    target: str,
    *,
    kind: str,
    legal_basis: str,
    receipt_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Walk legal forward edges until the mission reaches target."""
    emitted: list[TransitionReceiptV2] = []
    while csr.get_state(mission_id).current_state != target:
        current = csr.get_state(mission_id).current_state
        if _rank(target) < _rank(current):
            break
        nxt = _FORWARD_EDGE.get(current)
        if nxt is None:
            break
        if _rank(nxt) > _rank(target):
            break
        emitted.append(
            apply_mission_transition(
                csr,
                mission_id,
                to_state=nxt,
                kind=kind if nxt == target else "Decision",
                legal_basis=legal_basis if nxt == target else f"advance:{current}->{nxt}",
                receipt_id=receipt_id if nxt == target else None,
                payload=payload if nxt == target else None,
            )
        )
        if nxt == target:
            break
    return emitted


def advance_mission_blocked_path(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    legal_basis: str,
    payload: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Walk Challenged → Arbitrated → Remediated → Closed for blocked missions."""
    emitted: list[TransitionReceiptV2] = []
    current = csr.get_state(mission_id).current_state
    if current == "Observed":
        emitted.append(
            apply_mission_transition(
                csr,
                mission_id,
                to_state="Challenged",
                kind="Divergence",
                legal_basis=legal_basis,
                payload=payload,
            )
        )
    for to_state in _BLOCKED_PATH:
        if csr.get_state(mission_id).current_state == to_state:
            continue
        if csr.get_state(mission_id).current_state != _predecessor_for_blocked(to_state):
            break
        kind = "Remediation" if to_state == "Remediated" else "Divergence"
        if to_state == "Arbitrated":
            kind = "Remediation"
        if to_state == "Closed":
            kind = "Closure"
        emitted.append(
            apply_mission_transition(
                csr,
                mission_id,
                to_state=to_state,
                kind=kind,
                legal_basis=legal_basis,
                payload=payload if to_state == "Closed" else None,
            )
        )
    return emitted


def _predecessor_for_blocked(state: str) -> str:
    order = ["Observed", "Challenged", "Arbitrated", "Remediated", "Closed"]
    idx = order.index(state)
    return order[idx - 1]


def sync_mission_open_to_csr(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    ingress: dict[str, Any] | None = None,
) -> list[TransitionReceiptV2]:
    """Register mission and advance through Evaluated → Approved (mission accepted)."""
    try:
        csr.get_state(mission_id)
    except KeyError:
        register_mission_state(csr, mission_id, ingress=ingress)
    return advance_mission_to(
        csr,
        mission_id,
        "Approved",
        kind="Decision",
        legal_basis="mission_open:cloud_invariants_passed",
        payload={"ingress": dict(ingress or {})},
    )


def sync_mission_executing_to_csr(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    step_id: str | None = None,
) -> list[TransitionReceiptV2]:
    """Advance mission to Executed when step execution begins."""
    current = csr.get_state(mission_id).current_state
    if _rank(current) >= _rank("Executed"):
        return []
    return advance_mission_to(
        csr,
        mission_id,
        "Executed",
        kind="Observation",
        legal_basis="mission_executing",
        payload={"step_id": step_id} if step_id else None,
    )


def sync_mission_finalize_to_csr(
    csr: ConstitutionalStateRuntime,
    mission_id: str,
    *,
    urg_status: str,
    mission_receipt: dict[str, Any] | None = None,
    summary: str = "",
) -> list[TransitionReceiptV2]:
    """Sync constitutional state after mission completes (ok / blocked / rejected)."""
    try:
        csr.get_state(mission_id)
    except KeyError:
        if urg_status == "rejected":
            return []
        register_mission_state(csr, mission_id)
        advance_mission_to(
            csr,
            mission_id,
            "Approved",
            kind="Decision",
            legal_basis="mission_finalize:late_register",
        )

    receipt_id = None
    if mission_receipt:
        receipt_id = str(
            mission_receipt.get("receipt_id")
            or mission_receipt.get("ingress_stamp_hash")
            or f"mission-receipt-{mission_id}"
        )

    payload = {
        "urg_status": urg_status,
        "summary": summary,
        "mission_receipt_digest": stable_json_hash(mission_receipt or {}),
    }

    emitted: list[TransitionReceiptV2] = []
    current = csr.get_state(mission_id).current_state
    if _rank(current) < _rank("Observed"):
        emitted.extend(
            advance_mission_to(
                csr,
                mission_id,
                "Observed",
                kind="Observation",
                legal_basis=f"mission_finalize:{urg_status}",
                payload=payload,
            )
        )

    if urg_status == "blocked":
        emitted.extend(
            advance_mission_blocked_path(
                csr,
                mission_id,
                legal_basis="mission_blocked:cloud_invariant_failure",
                payload=payload,
            )
        )
    elif urg_status == "ok":
        emitted.extend(
            advance_mission_to(
                csr,
                mission_id,
                "Closed",
                kind="Closure",
                legal_basis="mission_completed",
                receipt_id=receipt_id,
                payload=payload,
            )
        )
    elif urg_status == "rejected":
        emitted.extend(
            advance_mission_to(
                csr,
                mission_id,
                "Closed",
                kind="Closure",
                legal_basis="mission_rejected",
                payload=payload,
            )
        )
    return emitted


def reconstruct_mission_state(csr: ConstitutionalStateRuntime, mission_id: str) -> StateObject:
    from constitutional.runtime import reconstruct_state

    receipts = csr.receipts_for(mission_id)
    return reconstruct_state(receipts, mission_id)


def replay_mission_state(csr: ConstitutionalStateRuntime, mission_id: str):
    return csr.replay(mission_id)
