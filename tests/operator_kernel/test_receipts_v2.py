"""Tests for Receipt v2 and Article XIV lifecycle models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from operator_kernel.receipts_v2 import (
    AccountabilityBlockV2,
    AuthorityBlockV2,
    ClosurePayloadV2,
    ClosureReceiptV2,
    ContinuityBlockV2,
    DecisionReceiptV2,
    DivergencePayloadV2,
    DivergenceReceiptV2,
    EvidenceBundleV2,
    EvidenceSufficiencyV2,
    ImpactBoundaryV2,
    InvariantBlockV2,
    LifecycleBlockV2,
    ObservationPayloadV2,
    ObservationReceiptV2,
    ReceiptInputsV2,
    ReceiptOutputsV2,
    RemediationPayloadV2,
    RemediationReceiptV2,
    ReproducibilityBlockV2,
    SignaturesBlockV2,
    closure_or_divergence_from_observation,
    compute_lineage_hash,
    is_receipt_v2_complete,
    new_receipt_id,
    observation_follows_decision,
    stable_json_hash,
    validate_lifecycle_transition,
)


def _base_blocks() -> dict:
    return {
        "inputs": ReceiptInputsV2(request_id="req-1", payload_hash="sha256:abc"),
        "outputs": ReceiptOutputsV2(status="executed", result_hash="sha256:def"),
        "invariant": InvariantBlockV2(
            name="workspace_integrity",
            description="Paths stay inside workspace jail",
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
            source="operator:builder",
            jurisdiction="workspace",
            legitimacy_basis="Article XIII",
        ),
        "reproducibility": ReproducibilityBlockV2(
            is_reproducible=True,
            mode="structural",
        ),
        "impact_boundary": ImpactBoundaryV2(
            scope_in=["workspace"],
            scope_out=["network", "secrets"],
        ),
        "accountability": AccountabilityBlockV2(primary_accountable_party="operator"),
        "signatures": SignaturesBlockV2(runtime_signature="sig-runtime"),
        "continuity": ContinuityBlockV2(lineage_hash="sha256:lineage"),
    }


def _decision_receipt() -> DecisionReceiptV2:
    rid = new_receipt_id("decision")
    return DecisionReceiptV2(
        receipt_id=rid,
        runtime="operator",
        timestamp="2026-06-23T12:00:00Z",
        action_type="tool_governance",
        lifecycle=LifecycleBlockV2(
            stage="decision",
            previous_stage_receipt_id=None,
            next_stage_expected="observation",
        ),
        **_base_blocks(),
    )


def test_is_receipt_v2_complete_true_for_decision() -> None:
    receipt = _decision_receipt()
    assert is_receipt_v2_complete(receipt)


def test_is_receipt_v2_complete_false_when_missing_lineage() -> None:
    receipt = _decision_receipt()
    receipt.continuity.lineage_hash = ""
    assert not is_receipt_v2_complete(receipt)


def test_decision_stage_validator_rejects_wrong_stage() -> None:
    with pytest.raises(ValidationError):
        DecisionReceiptV2(
            receipt_id=new_receipt_id(),
            runtime="operator",
            timestamp="2026-06-23T12:00:00Z",
            action_type="tool_governance",
            lifecycle=LifecycleBlockV2(stage="observation"),
            **_base_blocks(),
        )


def test_lifecycle_transition_decision_to_observation() -> None:
    decision = _decision_receipt()
    observation = ObservationReceiptV2(
        receipt_id=new_receipt_id("observation"),
        runtime="reality",
        timestamp="2026-06-23T12:01:00Z",
        action_type="outcome_observation",
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=decision.receipt_id,
            next_stage_expected="divergence_or_closure",
        ),
        observation=ObservationPayloadV2(
            observed_status="executed",
            observed_at="2026-06-23T12:01:00Z",
            observer_jurisdiction="reality",
        ),
        **_base_blocks(),
    )
    ok, reason = observation_follows_decision(decision, observation)
    assert ok, reason


def test_lifecycle_transition_rejects_skip() -> None:
    decision = _decision_receipt()
    remediation = RemediationReceiptV2(
        receipt_id=new_receipt_id("remediation"),
        runtime="institutional",
        timestamp="2026-06-23T12:02:00Z",
        action_type="remediation_plan",
        lifecycle=LifecycleBlockV2(
            stage="remediation",
            previous_stage_receipt_id=decision.receipt_id,
            next_stage_expected="closure",
        ),
        remediation=RemediationPayloadV2(
            required_actions=["revert patch"],
            responsible_party="operator",
            constitutional_trigger=False,
        ),
        **_base_blocks(),
    )
    ok, reason = validate_lifecycle_transition(decision, remediation)
    assert not ok
    assert "invalid transition" in reason


def test_divergence_to_remediation_to_closure_chain() -> None:
    decision = _decision_receipt()
    observation = ObservationReceiptV2(
        receipt_id=new_receipt_id("observation"),
        runtime="reality",
        timestamp="2026-06-23T12:01:00Z",
        action_type="outcome_observation",
        lifecycle=LifecycleBlockV2(
            stage="observation",
            previous_stage_receipt_id=decision.receipt_id,
            next_stage_expected="divergence_or_closure",
        ),
        observation=ObservationPayloadV2(
            observed_status="failed",
            observed_at="2026-06-23T12:01:00Z",
            observer_jurisdiction="reality",
        ),
        **_base_blocks(),
    )
    assert closure_or_divergence_from_observation(observation, reality_matches_expected=False) == "divergence"

    divergence = DivergenceReceiptV2(
        receipt_id=new_receipt_id("divergence"),
        runtime="reality",
        timestamp="2026-06-23T12:02:00Z",
        action_type="divergence_detected",
        lifecycle=LifecycleBlockV2(
            stage="divergence",
            previous_stage_receipt_id=observation.receipt_id,
            next_stage_expected="remediation",
        ),
        divergence=DivergencePayloadV2(
            nature="patch_not_applied",
            magnitude="high",
            evidence_receipt_ids=[observation.receipt_id],
        ),
        **_base_blocks(),
    )
    ok, _ = validate_lifecycle_transition(observation, divergence)
    assert ok

    remediation = RemediationReceiptV2(
        receipt_id=new_receipt_id("remediation"),
        runtime="institutional",
        timestamp="2026-06-23T12:03:00Z",
        action_type="remediation_plan",
        lifecycle=LifecycleBlockV2(
            stage="remediation",
            previous_stage_receipt_id=divergence.receipt_id,
            next_stage_expected="closure",
        ),
        remediation=RemediationPayloadV2(
            required_actions=["re-apply patch", "verify file hash"],
            responsible_party="operator",
            constitutional_trigger=True,
            escalation_path="constitutional-runtime",
        ),
        **_base_blocks(),
    )
    ok, _ = validate_lifecycle_transition(divergence, remediation)
    assert ok
    assert remediation.remediation.constitutional_trigger is True

    closure = ClosureReceiptV2(
        receipt_id=new_receipt_id("closure"),
        runtime="institutional",
        timestamp="2026-06-23T12:04:00Z",
        action_type="remediation_closed",
        lifecycle=LifecycleBlockV2(
            stage="closure",
            previous_stage_receipt_id=remediation.receipt_id,
            next_stage_expected=None,
        ),
        closure=ClosurePayloadV2(
            remediation_completed=True,
            restitution_delivered=True,
            institutional_review_performed=True,
            reviewing_body="institutional-runtime",
            constitutional_amendment_id="amd-001",
        ),
        **_base_blocks(),
    )
    ok, _ = validate_lifecycle_transition(remediation, closure)
    assert ok

    ok, reason = validate_lifecycle_transition(closure, decision)
    assert not ok
    assert "terminal" in reason or "invalid transition" in reason


def test_hash_helpers_are_stable() -> None:
    payload = {"a": 1, "b": [2, 3]}
    assert stable_json_hash(payload) == stable_json_hash(payload)
    lineage = compute_lineage_hash(
        previous_receipt_id="rcv2:prev",
        receipt_id="rcv2:curr",
        payload_hash="sha256:payload",
        previous_lineage_hash="sha256:parent",
    )
    assert lineage.startswith("sha256:")
