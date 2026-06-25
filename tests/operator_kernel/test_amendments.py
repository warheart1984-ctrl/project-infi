"""Tests for Article XVI Constitutional Amendment Process."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from operator_kernel.amendments import (
    AmendmentState,
    begin_amendment,
    process_amendment_receipts,
    replay_amendment,
)
from operator_kernel.receipts_v2 import (
    AMENDMENT_TRANSITIONS,
    AccountabilityBlockV2,
    AmendmentClosureReceiptV2,
    AmendmentEvaluationReceiptV2,
    AmendmentImplementationReceiptV2,
    AmendmentObservationReceiptV2,
    AmendmentPayloadV2,
    AmendmentProposalReceiptV2,
    AmendmentRatificationReceiptV2,
    AuthorityBlockV2,
    ContinuityBlockV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    RemediationPayloadV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    new_receipt_id,
    validate_amendment_transition,
    validate_immutable_amendment,
)


def _base_blocks(*, lifecycle_stage: str = "decision") -> dict:
    return {
        "inputs": ReceiptInputsV2(request_id="req-1", payload_hash="sha256:abc"),
        "outputs": ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        "invariant": InvariantBlockV2(
            name="constitutional_integrity",
            description="Amendments follow governed lifecycle",
            satisfied=True,
        ),
        "evidence": EvidenceBundleV2(
            bundle_id="evb-1",
            sufficiency=EvidenceSufficiencyV2(
                continuity=True,
                truth=True,
                sovereignty=True,
                institutional=True,
            ),
        ),
        "authority": AuthorityBlockV2(
            source="constitutional-runtime",
            jurisdiction="global",
            legitimacy_basis="Article XVI",
        ),
        "reproducibility": ReproducibilityBlockV2(is_reproducible=True, mode="exact"),
        "impact_boundary": ImpactBoundaryV2(scope_in=["constitution"], scope_out=["execution"]),
        "accountability": AccountabilityBlockV2(primary_accountable_party="constitutional-runtime"),
        "signatures": SignaturesBlockV2(runtime_signature="sig-runtime"),
        "continuity": ContinuityBlockV2(lineage_hash="sha256:lineage"),
        "lifecycle": LifecycleBlockV2(stage=lifecycle_stage),  # type: ignore[arg-type]
    }


def _trigger_receipt() -> RemediationReceiptV2:
    rid = new_receipt_id("remediation")
    return RemediationReceiptV2(
        receipt_id=rid,
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        action_type="remediation",
        remediation=RemediationPayloadV2(
            required_actions=["amend constitution"],
            responsible_party="sovereign",
            constitutional_trigger=True,
        ),
        **_base_blocks(lifecycle_stage="remediation"),
    )


def _amendment_receipt(stage: str, trigger_id: str, article: str = "XVII") -> AmendmentProposalReceiptV2:
    type_map = {
        "proposed": AmendmentProposalReceiptV2,
        "evaluated": AmendmentEvaluationReceiptV2,
        "ratified": AmendmentRatificationReceiptV2,
        "implemented": AmendmentImplementationReceiptV2,
        "observed": AmendmentObservationReceiptV2,
        "closed": AmendmentClosureReceiptV2,
    }
    cls = type_map[stage]
    return cls(
        receipt_id=new_receipt_id(f"amend-{stage}"),
        runtime="constitutional",
        timestamp="2026-06-23T12:00:00Z",
        amendment=AmendmentPayloadV2(
            article=article,
            change_type="addition",
            justification="new article required",
            trigger_receipt_id=trigger_id,
            amendment_stage=stage,  # type: ignore[arg-type]
        ),
        **_base_blocks(),
    )


def test_amendment_transition_graph() -> None:
    assert AMENDMENT_TRANSITIONS["proposed"] == ["evaluated"]
    assert AMENDMENT_TRANSITIONS["observed"] == ["closed"]
    validate_amendment_transition("proposed", "evaluated")


def test_amendment_transition_rejects_skip() -> None:
    with pytest.raises(ValueError, match="Illegal amendment transition"):
        validate_amendment_transition("proposed", "ratified")


def test_immutable_core_requires_override() -> None:
    payload = AmendmentPayloadV2(
        article="XVI",
        change_type="modification",
        justification="change core",
        trigger_receipt_id="trg-1",
        amendment_stage="proposed",
    )
    with pytest.raises(ValueError, match="immutable"):
        validate_immutable_amendment(payload)


def test_immutable_core_allows_override_with_ratification() -> None:
    payload = AmendmentPayloadV2(
        article="XVI",
        change_type="modification",
        justification="explicit override",
        trigger_receipt_id="trg-1",
        amendment_stage="proposed",
        immutable_override=True,
        unanimous_sovereign_ratification=True,
    )
    validate_immutable_amendment(payload)


def test_full_amendment_lifecycle() -> None:
    trigger = _trigger_receipt()
    stages = ["proposed", "evaluated", "ratified", "implemented", "observed", "closed"]
    receipts = [_amendment_receipt(s, trigger.receipt_id) for s in stages]
    state = process_amendment_receipts(trigger, receipts)
    assert state.current_stage == "closed"
    assert state.version == 6
    assert len(state.receipt_ids) == 6


def test_amendment_replay_matches_canonical() -> None:
    trigger = _trigger_receipt()
    stages = ["proposed", "evaluated", "ratified", "implemented", "observed", "closed"]
    receipts = [_amendment_receipt(s, trigger.receipt_id) for s in stages]
    canonical = process_amendment_receipts(trigger, receipts)
    result = replay_amendment(trigger, receipts, canonical)
    assert not result.diverged
    assert result.final_stage == "closed"


def test_amendment_replay_detects_divergence() -> None:
    trigger = _trigger_receipt()
    receipts = [_amendment_receipt("proposed", trigger.receipt_id)]
    canonical = begin_amendment(trigger, receipts[0])
    canonical.current_stage = "closed"
    result = replay_amendment(trigger, receipts, canonical)
    assert result.diverged


def test_proposal_stage_validator() -> None:
    trigger = _trigger_receipt()
    with pytest.raises(ValidationError):
        AmendmentProposalReceiptV2(
            receipt_id=new_receipt_id(),
            runtime="constitutional",
            timestamp="2026-06-23T12:00:00Z",
            amendment=AmendmentPayloadV2(
                article="XVII",
                change_type="addition",
                justification="bad stage",
                trigger_receipt_id=trigger.receipt_id,
                amendment_stage="evaluated",
            ),
            **_base_blocks(),
        )


def test_amendment_state_rejects_missing_trigger() -> None:
    trigger = _trigger_receipt()
    proposal = _amendment_receipt("proposed", "wrong-trigger-id")
    with pytest.raises(ValueError, match="trigger_receipt_id"):
        begin_amendment(trigger, proposal)
