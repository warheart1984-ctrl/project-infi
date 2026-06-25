"""Tests for Observer Verification Handbook."""

from __future__ import annotations

from operator_kernel.constitutional_state import StateObject, reconstruct_state
from operator_kernel.observer_verification import (
    ObserverVerificationContext,
    run_observer_verification,
)
from operator_kernel.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    DecisionReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    TransitionPayloadV2,
    TransitionReceiptV2,
    new_receipt_id,
)
from operator_kernel.transition_ledger import ConstitutionalTransitionLedger


def _base_blocks() -> dict:
    return {
        "inputs": ReceiptInputsV2(request_id="req-1", payload_hash="sha256:abc"),
        "outputs": ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        "invariant": InvariantBlockV2(name="verification", description="observer", satisfied=True),
        "evidence": EvidenceBundleV2(
            bundle_id="evb-1",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True, truth=True, sovereignty=True, institutional=True
            ),
        ),
        "authority": AuthorityBlockV2(
            source="observer", jurisdiction="external", legitimacy_basis="Article XVI"
        ),
        "reproducibility": ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        "impact_boundary": ImpactBoundaryV2(scope_in=["verification"], scope_out=["execution"]),
        "accountability": AccountabilityBlockV2(primary_accountable_party="observer"),
        "signatures": SignaturesBlockV2(runtime_signature="sig"),
        "continuity": ContinuityBlockV2(lineage_hash="sha256:lineage"),
    }


def _decision() -> DecisionReceiptV2:
    return DecisionReceiptV2(
        receipt_id=new_receipt_id("decision"),
        runtime="operator",
        timestamp="2026-06-23T12:00:00Z",
        action_type="tool_governance",
        lifecycle=LifecycleBlockV2(stage="decision"),
        **_base_blocks(),
    )


def _transition(from_state: str, to_state: str) -> TransitionReceiptV2:
    return TransitionReceiptV2(
        receipt_id=new_receipt_id("transition"),
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        action_type="state_transition",
        lifecycle=LifecycleBlockV2(stage="decision"),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis="Article XV",
            receipt_ids_used=[],
            state_id="claim-001",
        ),
        **_base_blocks(),
    )


def _claim_state() -> StateObject:
    return StateObject(
        state_id="claim-001",
        state_type="ClaimState",
        invariants=["evidential_integrity"],
        evidence_requirements=["bundle_id"],
        authority_model=["sovereignty-runtime"],
        reproducibility_requirements=["exact"],
        impact_boundaries=["workspace"],
        accountability_chain=["operator"],
    )


def test_observer_verification_success() -> None:
    receipts = [_transition("Proposed", "Evaluated"), _transition("Evaluated", "Approved")]
    canonical = reconstruct_state(receipts, _claim_state())
    ledger = ConstitutionalTransitionLedger()
    for r in receipts:
        ledger.append_from_transition_receipt(r, state_object_id="claim-001", accountable_party="op")

    report = run_observer_verification(
        ObserverVerificationContext(
            target_id="claim-001",
            receipts=[_decision()],
            transition_receipts=receipts,
            canonical_state=canonical,
            ledger=ledger,
            responsible_parties=["operator"],
        )
    )
    assert not report.failures
    assert report.verification_receipt is not None
    assert report.verification.state_reconstructed
    assert report.verification.state_replayed
    assert report.closure_receipt is not None


def test_observer_verification_failure_emits_divergence() -> None:
    receipts = [_transition("Proposed", "Evaluated")]
    canonical = reconstruct_state(receipts, _claim_state())
    canonical.current_state = "Closed"  # tamper

    report = run_observer_verification(
        ObserverVerificationContext(
            target_id="claim-001",
            transition_receipts=receipts,
            canonical_state=canonical,
        )
    )
    assert report.failures
    assert report.divergence_receipt is not None
    assert report.remediation_request_receipt is not None
    assert report.verification.divergence_detected
