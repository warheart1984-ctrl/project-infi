"""FCP-1 federated continuity protocol tests."""

from __future__ import annotations

from src.continuity.fcp import (
    ContinuityArtifact,
    FCPVersionSet,
    FederationProofBundle,
    FederationStatus,
    NodeContinuityProfile,
    NodeDescriptor,
    establish_federation,
    verify_federated_artifact,
)


def _node(node_id: str) -> NodeDescriptor:
    return NodeDescriptor(
        node_id=node_id,
        node_public_key=f"pub.{node_id}",
        profile=NodeContinuityProfile(
            resonance_signature="theta:1001",
            coherence_thresholds={
                "identity_min": 0.90,
                "governance_identity_tau": 0.84,
                "resonance_delta_max": 0.10,
            },
            identity_lineage_roots=("root:jon-halstead",),
            governance_invariants=(
                "ugr.identity_continuity",
                "ugr.authority_continuity",
                "ugr.duality.bidirectional_coherence",
                "ugr.duality.symmetric_constraints",
                "ugr.evidence_integrity",
                "ugr.law_surface_binding",
                "ugr.continuity_unifier",
            ),
        ),
        supported_versions=FCPVersionSet(
            wave_math="stage1.wave_math.v1",
            substrate="stage2.continuity_substrate.v1",
            kernel="stage3.two_kernel.v1",
            coupling="stage4.identity_computation_coupling.v1",
        ),
    )


def _proofs() -> FederationProofBundle:
    return FederationProofBundle(
        replay_proof=True,
        meaning_proof=True,
        identity_coherence_proof=True,
        governance_coherence_proof=True,
    )


def test_fcp1_establishes_federation_and_accepts_replay_stable_artifact() -> None:
    session = establish_federation(_node("node.alpha"), _node("node.beta"), _proofs())

    artifact = ContinuityArtifact(
        artifact_id="artifact.thread.1001",
        artifact_type="ContinuityThread",
        sender_node_id="node.beta",
        thread_id="ct.fcp.1001",
        trace_hash="hash.trace",
        replay_hash="hash.trace",
        reconstruction_hash="hash.reconstruction",
        sender_reconstruction_hash="hash.reconstruction",
        identity_coherence=0.95,
        governance_coherence=0.94,
        resonance_delta=0.03,
        identity_lineage_segments=("root:jon-halstead/segment:1",),
        governance_lineage_segments=("ugr:v1/segment:1",),
        signature="sig.beta.artifact.thread.1001",
    )
    decision = verify_federated_artifact(session, artifact)

    assert session.status is FederationStatus.ESTABLISHED
    assert decision.accepted is True
    assert decision.status is FederationStatus.ESTABLISHED
    assert decision.proofs["replay"] is True
    assert decision.proofs["meaning_reconstruction"] is True
    assert decision.proofs["identity_coherence"] is True
    assert decision.proofs["governance_coherence"] is True
    assert decision.proofs["resonance_stability"] is True


def test_fcp1_rejects_fractured_artifact_and_enters_safe_mode() -> None:
    session = establish_federation(_node("node.alpha"), _node("node.beta"), _proofs())
    artifact = ContinuityArtifact(
        artifact_id="artifact.fracture.1001",
        artifact_type="ContinuityEvent",
        sender_node_id="node.beta",
        thread_id="ct.fcp.fracture",
        trace_hash="hash.trace",
        replay_hash="hash.mutated",
        reconstruction_hash="hash.reconstruction",
        sender_reconstruction_hash="hash.reconstruction",
        identity_coherence=0.70,
        governance_coherence=0.60,
        resonance_delta=0.40,
        identity_lineage_segments=("root:jon-halstead/segment:2",),
        governance_lineage_segments=("ugr:v1/segment:2",),
        signature="sig.beta.artifact.fracture.1001",
    )
    decision = verify_federated_artifact(session, artifact)

    assert decision.accepted is False
    assert decision.status is FederationStatus.SAFE_MODE
    assert session.status is FederationStatus.SAFE_MODE
    assert "fcp.replay_proof_failed" in decision.violations
    assert "fcp.identity_coherence_failed" in decision.violations
    assert "fcp.resonance_divergence" in decision.violations
