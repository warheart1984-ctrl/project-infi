"""Tests for simplified Receipt v2 models."""

from __future__ import annotations

from receipts.models import (
    RECEIPT_LIFECYCLE_GRAPH,
    ReceiptV2,
    SixDimensionContract,
    from_transition_receipt_v2,
)


def test_lifecycle_graph_closure_terminal() -> None:
    assert RECEIPT_LIFECYCLE_GRAPH["Closure"] == []


def test_from_transition_receipt_roundtrip_shape() -> None:
    from operator_kernel.constitutional_task import build_operator_transition_receipt
    from constitutional.runtime import ConstitutionalStateRuntime
    from operator_kernel.constitutional_task import register_operator_task

    csr = ConstitutionalStateRuntime()
    register_operator_task(csr, "t1", goal="test")
    receipt = build_operator_transition_receipt(
        csr,
        "t1",
        from_state="Proposed",
        to_state="Evaluated",
        kind="Decision",
        legal_basis="test",
    )
    simplified = from_transition_receipt_v2(receipt)
    assert simplified.receipt_id == receipt.receipt_id
    assert simplified.state_object_id == "t1"
    assert simplified.contract.invariant


def test_receipt_v2_model() -> None:
    r = ReceiptV2(
        receipt_id="r1",
        kind="Decision",
        runtime="TestRuntime",
        state_object_id="s1",
        state_type="mission",
        contract=SixDimensionContract(
            invariant="test",
            accountable_party="op",
            impact_boundary="local",
        ),
    )
    assert r.kind == "Decision"
