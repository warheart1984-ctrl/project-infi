"""FCP-1 federated continuity protocol core.

FCP-1 is the in-process standards-track model for cross-node continuity
handshake, proof verification, artifact exchange, and fracture prevention.
Transport can be layered above this module later; this file owns the continuity
semantics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


FCP_PROTOCOL_VERSION = "fcp-1.draft"


class FederationStatus(str, Enum):
    DISCOVERY = "DISCOVERY"
    DENIED = "DENIED"
    ESTABLISHED = "ESTABLISHED"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    SAFE_MODE = "SAFE_MODE"
    TERMINATED = "TERMINATED"


@dataclass(frozen=True, slots=True)
class FCPVersionSet:
    wave_math: str
    substrate: str
    kernel: str
    coupling: str

    def compatible_with(self, other: "FCPVersionSet") -> bool:
        return self == other


@dataclass(frozen=True, slots=True)
class NodeContinuityProfile:
    resonance_signature: str
    coherence_thresholds: dict[str, float]
    identity_lineage_roots: tuple[str, ...]
    governance_invariants: tuple[str, ...]

    @property
    def identity_min(self) -> float:
        return float(self.coherence_thresholds.get("identity_min", 0.0))

    @property
    def governance_identity_tau(self) -> float:
        return float(self.coherence_thresholds.get("governance_identity_tau", 0.0))

    @property
    def resonance_delta_max(self) -> float:
        return float(self.coherence_thresholds.get("resonance_delta_max", 1.0))


@dataclass(frozen=True, slots=True)
class NodeDescriptor:
    node_id: str
    node_public_key: str
    profile: NodeContinuityProfile
    supported_versions: FCPVersionSet


@dataclass(frozen=True, slots=True)
class FederationProofBundle:
    replay_proof: bool
    meaning_proof: bool
    identity_coherence_proof: bool
    governance_coherence_proof: bool

    def proofs(self) -> dict[str, bool]:
        return {
            "replay": self.replay_proof,
            "meaning_reconstruction": self.meaning_proof,
            "identity_coherence": self.identity_coherence_proof,
            "governance_coherence": self.governance_coherence_proof,
        }

    def all_valid(self) -> bool:
        return all(self.proofs().values())


@dataclass(frozen=True, slots=True)
class ContinuityArtifact:
    artifact_id: str
    artifact_type: str
    sender_node_id: str
    thread_id: str
    trace_hash: str
    replay_hash: str
    reconstruction_hash: str
    sender_reconstruction_hash: str
    identity_coherence: float
    governance_coherence: float
    resonance_delta: float
    identity_lineage_segments: tuple[str, ...]
    governance_lineage_segments: tuple[str, ...]
    signature: str
    immutable: bool = True
    reconstructable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FederationSession:
    protocol_version: str
    local_node: NodeDescriptor
    remote_node: NodeDescriptor
    status: FederationStatus
    thresholds: dict[str, float]
    handshake_phases: tuple[str, ...]
    proofs: dict[str, bool]
    violations: list[str] = field(default_factory=list)
    accepted_artifacts: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ArtifactDecision:
    artifact_id: str
    accepted: bool
    status: FederationStatus
    proofs: dict[str, bool]
    violations: tuple[str, ...]


def _lineage_roots_overlap(local: NodeDescriptor, remote: NodeDescriptor) -> bool:
    return bool(set(local.profile.identity_lineage_roots) & set(remote.profile.identity_lineage_roots))


def _governance_invariants_compatible(local: NodeDescriptor, remote: NodeDescriptor) -> bool:
    return set(local.profile.governance_invariants) == set(remote.profile.governance_invariants)


def _combined_thresholds(local: NodeDescriptor, remote: NodeDescriptor) -> dict[str, float]:
    return {
        "identity_min": max(local.profile.identity_min, remote.profile.identity_min),
        "governance_identity_tau": max(
            local.profile.governance_identity_tau,
            remote.profile.governance_identity_tau,
        ),
        "resonance_delta_max": min(
            local.profile.resonance_delta_max,
            remote.profile.resonance_delta_max,
        ),
    }


def _compatibility_violations(local: NodeDescriptor, remote: NodeDescriptor) -> list[str]:
    violations: list[str] = []
    if not local.supported_versions.compatible_with(remote.supported_versions):
        violations.append("fcp.version_incompatible")
    if local.profile.resonance_signature != remote.profile.resonance_signature:
        violations.append("fcp.resonance_signature_incompatible")
    if not _lineage_roots_overlap(local, remote):
        violations.append("fcp.identity_roots_incompatible")
    if not _governance_invariants_compatible(local, remote):
        violations.append("fcp.governance_invariants_incompatible")
    return violations


def establish_federation(
    local_node: NodeDescriptor,
    remote_node: NodeDescriptor,
    proofs: FederationProofBundle,
) -> FederationSession:
    """Run the FCP-1 four-phase federation handshake."""

    violations = _compatibility_violations(local_node, remote_node)
    proof_map = proofs.proofs()
    for proof_name, passed in proof_map.items():
        if not passed:
            violations.append(f"fcp.handshake_{proof_name}_proof_failed")
    status = FederationStatus.ESTABLISHED if not violations else FederationStatus.DENIED
    return FederationSession(
        protocol_version=FCP_PROTOCOL_VERSION,
        local_node=local_node,
        remote_node=remote_node,
        status=status,
        thresholds=_combined_thresholds(local_node, remote_node),
        handshake_phases=(
            "DISCOVERY",
            "COMPATIBILITY_CHECK",
            "CONTINUITY_PROOF_EXCHANGE",
            "FEDERATION_ESTABLISHMENT",
        ),
        proofs=proof_map,
        violations=violations,
    )


def _segment_extends_any_root(segment: str, roots: tuple[str, ...]) -> bool:
    return any(segment == root or segment.startswith(f"{root}/") for root in roots)


def _artifact_proofs(session: FederationSession, artifact: ContinuityArtifact) -> dict[str, bool]:
    identity_min = session.thresholds["identity_min"]
    tau = session.thresholds["governance_identity_tau"]
    resonance_delta_max = session.thresholds["resonance_delta_max"]
    lineage_roots = (
        session.local_node.profile.identity_lineage_roots
        + session.remote_node.profile.identity_lineage_roots
    )
    return {
        "immutable": artifact.immutable,
        "signed": bool(artifact.signature),
        "replay": bool(artifact.trace_hash) and artifact.trace_hash == artifact.replay_hash,
        "meaning_reconstruction": (
            artifact.reconstructable
            and bool(artifact.reconstruction_hash)
            and artifact.reconstruction_hash == artifact.sender_reconstruction_hash
        ),
        "identity_coherence": artifact.identity_coherence >= identity_min,
        "governance_coherence": (artifact.governance_coherence * artifact.identity_coherence) >= tau,
        "resonance_stability": artifact.resonance_delta <= resonance_delta_max,
        "identity_lineage_extension": all(
            _segment_extends_any_root(segment, lineage_roots)
            for segment in artifact.identity_lineage_segments
        ),
        "governance_lineage_extension": bool(artifact.governance_lineage_segments),
    }


def _artifact_violations(proofs: dict[str, bool]) -> list[str]:
    violation_by_proof = {
        "immutable": "fcp.artifact_mutable",
        "signed": "fcp.artifact_unsigned",
        "replay": "fcp.replay_proof_failed",
        "meaning_reconstruction": "fcp.meaning_reconstruction_failed",
        "identity_coherence": "fcp.identity_coherence_failed",
        "governance_coherence": "fcp.governance_coherence_failed",
        "resonance_stability": "fcp.resonance_divergence",
        "identity_lineage_extension": "fcp.identity_lineage_overwrite_attempt",
        "governance_lineage_extension": "fcp.governance_lineage_missing",
    }
    return [violation_by_proof[name] for name, passed in proofs.items() if not passed]


def _status_for_violations(violations: list[str]) -> FederationStatus:
    if not violations:
        return FederationStatus.ESTABLISHED
    severe = {
        "fcp.artifact_mutable",
        "fcp.artifact_unsigned",
        "fcp.replay_proof_failed",
        "fcp.meaning_reconstruction_failed",
        "fcp.identity_coherence_failed",
        "fcp.resonance_divergence",
        "fcp.identity_lineage_overwrite_attempt",
    }
    if severe & set(violations):
        return FederationStatus.SAFE_MODE
    return FederationStatus.DEGRADED


def verify_federated_artifact(
    session: FederationSession,
    artifact: ContinuityArtifact,
) -> ArtifactDecision:
    """Verify a continuity artifact against FCP-1 proof and fracture rules."""

    if session.status is not FederationStatus.ESTABLISHED:
        violations = ["fcp.federation_not_established"]
        return ArtifactDecision(
            artifact_id=artifact.artifact_id,
            accepted=False,
            status=session.status,
            proofs={},
            violations=tuple(violations),
        )
    if artifact.sender_node_id not in {session.local_node.node_id, session.remote_node.node_id}:
        proofs = {"sender_known": False}
        violations = ["fcp.sender_not_in_federation"]
        session.status = FederationStatus.SAFE_MODE
        return ArtifactDecision(
            artifact_id=artifact.artifact_id,
            accepted=False,
            status=session.status,
            proofs=proofs,
            violations=tuple(violations),
        )

    proofs = _artifact_proofs(session, artifact)
    violations = _artifact_violations(proofs)
    session.status = _status_for_violations(violations)
    accepted = not violations
    if accepted:
        session.accepted_artifacts.append(artifact.artifact_id)
    return ArtifactDecision(
        artifact_id=artifact.artifact_id,
        accepted=accepted,
        status=session.status,
        proofs=proofs,
        violations=tuple(violations),
    )
