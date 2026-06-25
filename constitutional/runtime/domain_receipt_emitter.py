"""Build ObservationReceiptV2 for domain runtime facades."""

from __future__ import annotations

from typing import Any

from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass

from constitutional.runtime.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ObservationReceiptV2,
    ReceiptContextV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    compute_lineage_hash,
    new_receipt_id,
    stable_json_hash,
    utc_now_rfc3339,
)

ACCOUNTABLE_PARTY = "Architect"


def build_domain_observation_receipt(
    *,
    runtime: str,
    state_object_id: str,
    action_type: str,
    kind: str,
    invariant_name: str,
    invariant_description: str,
    payload: dict[str, Any],
    impact_scope_in: list[str],
    impact_scope_out: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    thread_id: str | None = None,
    previous_receipt_id: str | None = None,
    previous_lineage_hash: str | None = None,
    observed_status: str | None = None,
    threats: list[ReconstructabilityFailureClass] | None = None,
) -> ObservationReceiptV2:
    """Emit a six-dimension observation receipt (Article XIV observation stage)."""
    rid = new_receipt_id(runtime.lower().replace("runtime", ""))
    payload_hash = stable_json_hash(payload)
    lineage = compute_lineage_hash(
        previous_receipt_id=previous_receipt_id,
        receipt_id=rid,
        payload_hash=payload_hash,
        previous_lineage_hash=previous_lineage_hash,
    )
    now = utc_now_rfc3339()
    return ObservationReceiptV2(
        receipt_id=rid,
        runtime=runtime,
        timestamp=now,
        action_type=action_type,
        inputs=ReceiptInputsV2(
            request_id=state_object_id,
            payload_hash=payload_hash,
            context=ReceiptContextV2(task_id=thread_id or state_object_id),
        ),
        outputs=ReceiptOutputsV2(status=kind, result_hash=payload_hash),
        invariant=InvariantBlockV2(
            name=invariant_name,
            description=invariant_description,
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id=f"evb-{state_object_id}",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
            sources=[],
        ),
        authority=AuthorityBlockV2(
            source=runtime,
            jurisdiction="founder_governance",
            legitimacy_basis="runtime_law_spine",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(
            scope_in=impact_scope_in,
            scope_out=impact_scope_out or ["external_unconfigured"],
        ),
        accountability=AccountabilityBlockV2(primary_accountable_party=ACCOUNTABLE_PARTY),
        signatures=SignaturesBlockV2(runtime_signature=f"{runtime}:v0"),
        continuity=ContinuityBlockV2(
            previous_receipt_id=previous_receipt_id,
            thread_id=thread_id or state_object_id,
            lineage_hash=lineage,
        ),
        lifecycle=LifecycleBlockV2(stage="observation"),
        observation=ObservationPayloadV2(
            observed_status=observed_status or kind,
            observed_at=now,
            observer_jurisdiction=runtime,
            notes=stable_json_hash(payload),
        ),
        threats=list(threats or []),
    )
