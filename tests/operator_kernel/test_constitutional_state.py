"""Tests for Article XV Constitutional State Runtime."""

from __future__ import annotations

import pytest

from operator_kernel.constitutional_state import (
    LEGAL_TRANSITIONS,
    ReplayResult,
    StateObject,
    StateTransition,
    map_domain_state,
    reconstruct_state,
    reconstruct_state_at,
    replay_state,
    validate_transition,
)
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


def _transition_receipt(
    from_state: str,
    to_state: str,
    *,
    state_id: str = "claim-001",
) -> TransitionReceiptV2:
    rid = new_receipt_id("transition")
    return TransitionReceiptV2(
        receipt_id=rid,
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        action_type="state_transition",
        inputs=ReceiptInputsV2(request_id="req-1", payload_hash="sha256:abc"),
        outputs=ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        invariant=InvariantBlockV2(
            name="state_legality",
            description="Transitions follow constitutional graph",
            satisfied=True,
        ),
        evidence=EvidenceBundleV2(
            bundle_id="evb-1",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        authority=AuthorityBlockV2(
            source="constitutional-runtime",
            jurisdiction="global",
            legitimacy_basis="Article XV",
        ),
        reproducibility=ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        impact_boundary=ImpactBoundaryV2(scope_in=["constitutional-state"], scope_out=["external"]),
        accountability=AccountabilityBlockV2(primary_accountable_party="constitutional-runtime"),
        signatures=SignaturesBlockV2(runtime_signature="sig-runtime"),
        continuity=ContinuityBlockV2(lineage_hash="sha256:lineage"),
        lifecycle=LifecycleBlockV2(stage="decision"),
        transition=TransitionPayloadV2(
            from_state=from_state,
            to_state=to_state,
            legal_basis="Article XV §4",
            receipt_ids_used=[],
            state_id=state_id,
            state_type="ClaimState",
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


def test_legal_transition_graph_matches_spec() -> None:
    assert LEGAL_TRANSITIONS["Proposed"] == ["Evaluated"]
    assert "Closed" in LEGAL_TRANSITIONS["Observed"]
    assert LEGAL_TRANSITIONS["Remediated"] == ["Closed"]


def test_validate_transition_rejects_illegal_edge() -> None:
    with pytest.raises(ValueError, match="Illegal transition"):
        validate_transition("Proposed", "Closed")


def test_map_domain_state_truth() -> None:
    assert map_domain_state("Truth", "Verified") == "Approved"
    assert map_domain_state("Truth", "Unknown") == "Unknown"


def test_reconstruct_state_happy_path_to_closed() -> None:
    state = _claim_state()
    receipts = [
        _transition_receipt("Proposed", "Evaluated"),
        _transition_receipt("Evaluated", "Approved"),
        _transition_receipt("Approved", "Executed"),
        _transition_receipt("Executed", "Observed"),
        _transition_receipt("Observed", "Closed"),
    ]
    final = reconstruct_state(receipts, state)
    assert final.current_state == "Closed"
    assert final.version == 5
    assert len(final.history) == 5


def test_reconstruct_state_at_historical_point() -> None:
    state = _claim_state()
    receipts = [
        _transition_receipt("Proposed", "Evaluated"),
        _transition_receipt("Evaluated", "Approved"),
        _transition_receipt("Approved", "Executed"),
    ]
    at_two = reconstruct_state_at(receipts, state, at_index=1)
    assert at_two.current_state == "Approved"
    assert at_two.version == 2


def test_apply_transition_rejects_wrong_from_state() -> None:
    state = _claim_state()
    from constitutional.core.models import Transition

    with pytest.raises(ValueError, match="Illegal transition"):
        state.apply_transition(
            Transition(
                state_object_id="claim-001",
                from_state="Evaluated",
                to_state="Approved",
                receipt_id="r1",
                runtime="test",
                legal_basis="test",
                accountable_party="operator",
            )
        )


def test_replay_state_matches_canonical() -> None:
    state = _claim_state()
    receipts = [
        _transition_receipt("Proposed", "Evaluated"),
        _transition_receipt("Evaluated", "Approved"),
        _transition_receipt("Approved", "Executed"),
        _transition_receipt("Executed", "Observed"),
        _transition_receipt("Observed", "Closed"),
    ]
    canonical = reconstruct_state(receipts, state.model_copy(deep=True))
    result = replay_state(receipts, canonical)
    assert isinstance(result, ReplayResult)
    assert not result.diverged
    assert result.reconstructed_state == "Closed"
    assert result.history_length == 5


def test_replay_state_detects_divergence() -> None:
    state = _claim_state()
    receipts = [
        _transition_receipt("Proposed", "Evaluated"),
        _transition_receipt("Evaluated", "Approved"),
    ]
    canonical = reconstruct_state(receipts, state.model_copy(deep=True))
    # Tamper canonical state
    canonical.current_state = "Closed"
    canonical.version = 99
    result = replay_state(receipts, canonical)
    assert result.diverged
