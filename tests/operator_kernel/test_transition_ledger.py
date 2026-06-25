"""Tests for Constitutional Transition Ledger."""

from __future__ import annotations

from operator_kernel.constitutional_state import StateObject, reconstruct_state
from operator_kernel.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
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


def _transition_receipt(from_state: str, to_state: str) -> TransitionReceiptV2:
    rid = new_receipt_id("transition")
    return TransitionReceiptV2(
        receipt_id=rid,
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        action_type="state_transition",
        inputs=ReceiptInputsV2(request_id="req-1", payload_hash="sha256:abc"),
        outputs=ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        invariant=InvariantBlockV2(name="state_legality", description="legal", satisfied=True),
        evidence=EvidenceBundleV2(
            bundle_id="evb-1",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True, truth=True, sovereignty=True, institutional=True
            ),
        ),
        authority=AuthorityBlockV2(
            source="constitutional-runtime", jurisdiction="global", legitimacy_basis="Article XV"
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(scope_in=["state"], scope_out=["external"]),
        accountability=AccountabilityBlockV2(primary_accountable_party="operator"),
        signatures=SignaturesBlockV2(runtime_signature="sig"),
        continuity=ContinuityBlockV2(lineage_hash="sha256:lineage"),
        lifecycle=LifecycleBlockV2(stage="decision"),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis="Article XV",
            receipt_ids_used=[],
            state_id="claim-001",
        ),
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


def test_ledger_append_and_snapshot_hash() -> None:
    ledger = ConstitutionalTransitionLedger()
    receipt = _transition_receipt("Proposed", "Evaluated")
    entry = ledger.append_from_transition_receipt(
        receipt, state_object_id="claim-001", accountable_party="operator"
    )
    assert entry.receipt_id == receipt.receipt_id
    assert ledger.snapshot_hash().startswith("sha256:")


def test_ledger_detects_broken_lineage() -> None:
    ledger = ConstitutionalTransitionLedger()
    r1 = _transition_receipt("Proposed", "Evaluated")
    r2 = _transition_receipt("Approved", "Executed")  # skips Evaluated -> Approved
    ledger.append_from_transition_receipt(r1, state_object_id="claim-001", accountable_party="op")
    ledger.append_from_transition_receipt(r2, state_object_id="claim-001", accountable_party="op")
    failures = ledger.detect_failures()
    codes = {f.code for f in failures}
    assert "broken_lineage" in codes


def test_ledger_replay_success() -> None:
    ledger = ConstitutionalTransitionLedger()
    receipts = [
        _transition_receipt("Proposed", "Evaluated"),
        _transition_receipt("Evaluated", "Approved"),
    ]
    for r in receipts:
        ledger.append_from_transition_receipt(r, state_object_id="claim-001", accountable_party="op")
    canonical = reconstruct_state(receipts, _claim_state())
    result = ledger.replay(receipts, canonical)
    assert not result.state_replay_diverged
    assert not any(f.code == "irreproducible_transition" for f in result.failures)


def test_ledger_jsonl_roundtrip(tmp_path) -> None:
    ledger = ConstitutionalTransitionLedger()
    receipt = _transition_receipt("Proposed", "Evaluated")
    ledger.append_from_transition_receipt(receipt, state_object_id="claim-001", accountable_party="op")
    path = tmp_path / "ledger.jsonl"
    ledger.save_jsonl(path)
    loaded = ConstitutionalTransitionLedger.load_jsonl(path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].receipt_id == receipt.receipt_id
