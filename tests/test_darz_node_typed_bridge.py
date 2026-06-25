"""DAR-Z node substrate typed bridge tests."""

from __future__ import annotations

from src.darz_kernel_bridge import (
    DarzBridgeInput,
    DarzNodeAdvertisement,
    build_darz_bridge_receipt,
    darz_bridge_summary,
)


def _bridge_input(node: DarzNodeAdvertisement) -> DarzBridgeInput:
    return DarzBridgeInput(
        ugr_trace_id="ct.nova.typed-darz-bridge-1001",
        ugr_proof_id="proof.nova.typed-darz-bridge-1001",
        ugr_proof_status="PROVEN",
        ugr_cvr_id="cvr.nova.typed-darz-bridge-1001",
        ugr_cvr_score=1.0,
        ugr_trace_hash="hash.trace",
        ugr_replay_hash="hash.trace",
        aais_status="completed",
        aais_trace_stages=["aris_admit", "jarvis_authorize", "cortex_execute", "speaking_emit"],
        tri_core_authority="tri_core",
        active_runtimes=["darz.continuity_kernel", "jarvis.reasoning"],
        darz_node=node,
        wave_signature={"A": 0.59, "f": 0.4, "phi": 0.97, "C": 0.9, "R": 0.7},
        cross_kernel_coherence={
            "C_comp": 0.92,
            "C_identity": 0.91,
            "C_pair": 0.8372,
            "delta_phi": 0.05,
            "delta_R": 0.04,
            "continuity_ok": True,
            "violations": [],
        },
        timestamp="2026-06-20T12:00:00Z",
    )


def test_darz_node_advertisement_becomes_typed_substrate_architecture_event() -> None:
    node = DarzNodeAdvertisement(
        node_id="darz.node.001",
        status="ACTIVE",
        threads=3,
        events=3,
        reconstruction="PASS",
        proof_status="PROVEN",
        federation_ready=True,
        genesis_threads=("founder.genesis", "identity.genesis", "darz.genesis"),
        proof_hash="proof.hash.1001",
    )

    receipt = build_darz_bridge_receipt(_bridge_input(node))
    summary = darz_bridge_summary(receipt)
    architecture_event = receipt["events"][1]
    decision_event = receipt["events"][-1]

    assert receipt["accepted"] is True
    assert receipt["substrate_binding"]["node_id"] == "darz.node.001"
    assert receipt["substrate_binding"]["role"] == "continuity_identity_substrate"
    assert receipt["darz_node"]["federation_ready"] is True
    assert architecture_event["event_type"] == "Architecture"
    assert architecture_event["payload"]["kind"] == "Architecture"
    assert architecture_event["payload"]["data"]["name"] == "DAR-Z Continuity and Identity Substrate"
    assert architecture_event["payload"]["data"]["components"] == [
        "founder.genesis",
        "identity.genesis",
        "darz.genesis",
    ]
    assert decision_event["payload"]["data"]["chosen_architecture"] == architecture_event["id"]
    assert architecture_event["id"] in decision_event["lineage"]
    for event in receipt["events"]:
        fields = event["bridge_fields"]
        assert fields["darz_node_id"] == "darz.node.001"
        assert fields["substrate_role"] == "continuity_identity_substrate"
        assert fields["bridge_hash"] == receipt["bridge_hash"]
        assert fields["lineage_pointers"] == event["lineage"]
        assert fields["wave_signature"]["C"] == 0.9
        assert fields["continuity_proof"]["proof_status"] == "PROVEN"
    assert summary["darz_node_id"] == "darz.node.001"
    assert summary["substrate_role"] == "continuity_identity_substrate"
    assert summary["wave_signature"]["C"] == 0.9
    assert summary["continuity_proof"]["replay_stable"] is True
    assert summary["cross_kernel_coherence"]["continuity_ok"] is True


def test_darz_node_bridge_rejects_non_proven_node_advertisement() -> None:
    node = DarzNodeAdvertisement(
        node_id="darz.node.001",
        status="ACTIVE",
        threads=3,
        events=3,
        reconstruction="PASS",
        proof_status="ASSERTED",
        federation_ready=True,
        genesis_threads=("founder.genesis", "identity.genesis", "darz.genesis"),
        proof_hash="proof.hash.1001",
    )

    receipt = build_darz_bridge_receipt(_bridge_input(node))

    assert receipt["accepted"] is False
    assert "darz.node.proof_not_proven" in receipt["violations"]
