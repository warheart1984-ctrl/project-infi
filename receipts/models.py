"""Simplified Receipt v2 models (Article XIII) with adapters to constitutional_substrate."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

ReceiptKind = Literal[
    "Decision",
    "Observation",
    "Divergence",
    "Arbitration",
    "Remediation",
    "Closure",
]

RECEIPT_LIFECYCLE_GRAPH: dict[ReceiptKind, list[ReceiptKind]] = {
    "Decision": ["Observation"],
    "Observation": ["Divergence", "Closure"],
    "Divergence": ["Arbitration", "Remediation"],
    "Arbitration": ["Remediation", "Closure"],
    "Remediation": ["Closure"],
    "Closure": [],
}


class SixDimensionContract(BaseModel):
    invariant: str
    evidence_ids: List[str] = Field(default_factory=list)
    authority_chain: List[str] = Field(default_factory=list)
    reproducible: bool = True
    impact_boundary: str = ""
    accountable_party: str = ""


class ReceiptV2(BaseModel):
    receipt_id: str
    kind: ReceiptKind
    runtime: str
    state_object_id: str
    state_type: str
    contract: SixDimensionContract
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lifecycle_prev: Optional[ReceiptKind] = None
    lifecycle_next: Optional[ReceiptKind] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class TruthPayload(BaseModel):
    claim_id: str
    claim_text: str
    verdict: Literal["supported", "verified", "rejected", "uncertain"]
    confidence: float
    evidence_bundle_id: str


class TruthReceipt(ReceiptV2):
    runtime: Literal["TruthVerificationRuntime"] = "TruthVerificationRuntime"
    payload: TruthPayload  # type: ignore[assignment]


class SovereigntyPayload(BaseModel):
    grant_id: str
    subject_id: str
    authority_scope: str
    delegation_chain: List[str] = Field(default_factory=list)
    status: Literal["delegated", "active", "suspended", "revoked"]


class SovereigntyReceipt(ReceiptV2):
    runtime: Literal["SovereigntyRuntime"] = "SovereigntyRuntime"
    payload: SovereigntyPayload  # type: ignore[assignment]


class ReproductionPayload(BaseModel):
    original_receipt_id: str
    reproduction_run_id: str
    matched: bool
    divergence_summary: Optional[str] = None
    divergence_fields: List[str] = Field(default_factory=list)


class ReproductionReceipt(ReceiptV2):
    runtime: Literal["ReproductionRuntime"] = "ReproductionRuntime"
    payload: ReproductionPayload  # type: ignore[assignment]


def _kind_from_stage(stage: str) -> ReceiptKind:
    mapping: dict[str, ReceiptKind] = {
        "decision": "Decision",
        "observation": "Observation",
        "divergence": "Divergence",
        "arbitration": "Arbitration",
        "remediation": "Remediation",
        "closure": "Closure",
    }
    return mapping.get(stage.lower(), "Decision")


def from_transition_receipt_v2(receipt: Any) -> ReceiptV2:
    """Adapt constitutional_substrate TransitionReceiptV2 → simplified ReceiptV2."""
    transition = getattr(receipt, "transition", None)
    kind = _kind_from_stage(getattr(getattr(receipt, "lifecycle", None), "stage", "decision"))
    return ReceiptV2(
        receipt_id=receipt.receipt_id,
        kind=kind,
        runtime=receipt.runtime,
        state_object_id=(
            transition.state_id if transition else getattr(receipt.inputs, "request_id", "")
        ),
        state_type=transition.state_type if transition else "unknown",
        contract=SixDimensionContract(
            invariant=receipt.invariant.name,
            evidence_ids=[receipt.evidence.bundle_id],
            authority_chain=[
                receipt.authority.source,
                receipt.authority.jurisdiction,
            ],
            reproducible=bool(receipt.reproducibility.is_reproducible),
            impact_boundary=",".join(receipt.impact_boundary.scope_in),
            accountable_party=receipt.accountability.primary_accountable_party,
        ),
        timestamp=datetime.fromisoformat(str(receipt.timestamp).replace("Z", "+00:00")),
        lifecycle_prev=None,
        lifecycle_next=RECEIPT_LIFECYCLE_GRAPH.get(kind, [None])[0] if RECEIPT_LIFECYCLE_GRAPH.get(kind) else None,
        payload={
            "from_state": transition.from_state if transition else None,
            "to_state": transition.to_state if transition else None,
            "legal_basis": transition.legal_basis if transition else None,
            "action_type": receipt.action_type,
        },
    )


def to_transition_receipt_v2(
    receipt: ReceiptV2,
    *,
    from_state: str,
    to_state: str,
    legal_basis: str,
) -> Any:
    """Build constitutional_substrate TransitionReceiptV2 from simplified ReceiptV2."""
    from constitutional.runtime import new_receipt_id, stable_json_hash, utc_now_rfc3339
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
        TransitionReceiptV2,
        compute_lineage_hash,
    )

    rid = receipt.receipt_id or new_receipt_id("rcv2")
    payload_hash = stable_json_hash(receipt.payload)
    lineage = compute_lineage_hash(
        previous_receipt_id=None,
        receipt_id=rid,
        payload_hash=payload_hash,
        previous_lineage_hash=None,
    )
    return TransitionReceiptV2(
        receipt_id=rid,
        runtime=receipt.runtime,
        timestamp=utc_now_rfc3339(),
        action_type="state_transition",
        inputs=ReceiptInputsV2(
            request_id=receipt.state_object_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=receipt.state_object_id),
        ),
        outputs=ReceiptOutputsV2(status=receipt.kind.lower(), result_hash=payload_hash),
        invariant=InvariantBlockV2(
            name=receipt.contract.invariant,
            description=receipt.contract.invariant,
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=receipt.contract.evidence_ids[0] if receipt.contract.evidence_ids else f"evb-{rid}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source=receipt.contract.authority_chain[0] if receipt.contract.authority_chain else receipt.runtime,
            jurisdiction=receipt.contract.authority_chain[1] if len(receipt.contract.authority_chain) > 1 else "default",
            legitimacy_basis="receipt_v2",
        ),
        reproducibility=ReproducibilityBlockV2(
            is_reproducible=receipt.contract.reproducible,
            mode="exact",
        ),
        impact_boundary=ImpactBoundaryV2(
            scope_in=[receipt.contract.impact_boundary] if receipt.contract.impact_boundary else [],
            scope_out=[],
        ),
        accountability=AccountabilityBlockV2(
            primary_accountable_party=receipt.contract.accountable_party or "unknown",
        ),
        signatures=SignaturesBlockV2(runtime_signature=f"{receipt.runtime}:v2"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=None,
            thread_id=receipt.state_object_id,
            lineage_hash=lineage,
        ),
        lifecycle=LifecycleBlockV2(stage=receipt.kind.lower()),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis=legal_basis,
            receipt_ids_used=[],
            state_id=receipt.state_object_id,
            state_type=receipt.state_type,
        ),
    )
