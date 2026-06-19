"""Continuity-grade reputation and Continuity-Validated Reputation (CVR)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from src.continuity.ccs import CCSStore, continuity_trace_fingerprint, replay_trace_from_store
from src.continuity.proof import Proof, ProofStatus, valid_proof
from src.continuity.ugr_trace import (
    evaluate_trace_ugr_invariants,
    trace_authority_chain_strength,
    trace_continuity_score,
    trace_evidence_integrity_score,
)

DEFAULT_REPUTATION_LAW_SURFACES = ("ugr.continuity", "aais.reputation")


@dataclass(frozen=True)
class ReputationWeights:
    """Governance-tunable weights for continuity-grade derived_score."""

    alpha: float = 0.35  # proofs_replay_stable / proofs_count
    beta: float = 0.25  # continuity_score_avg
    gamma: float = 0.25  # evidence_integrity_avg
    delta: float = 0.15  # authority_chain_strength_avg
    epsilon: float = 0.05  # penalty per revoked proof


DEFAULT_REPUTATION_WEIGHTS = ReputationWeights()

# Preset documented in CONTINUITY_REPUTATION_V1.md worked examples.
EXAMPLE_REPUTATION_WEIGHTS = ReputationWeights(
    alpha=0.32,
    beta=0.25,
    gamma=0.25,
    delta=0.15,
    epsilon=0.05,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class ReputationMetrics:
    proofs_count: int = 0
    proofs_replay_stable: int = 0
    revoked_proofs: int = 0
    continuity_score_avg: float = 0.0
    evidence_integrity_avg: float = 0.0
    authority_chain_strength_avg: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "proofs_count": self.proofs_count,
            "proofs_replay_stable": self.proofs_replay_stable,
            "revoked_proofs": self.revoked_proofs,
            "continuity_score_avg": self.continuity_score_avg,
            "evidence_integrity_avg": self.evidence_integrity_avg,
            "authority_chain_strength_avg": self.authority_chain_strength_avg,
        }


def compute_derived_score(
    metrics: ReputationMetrics,
    weights: ReputationWeights = DEFAULT_REPUTATION_WEIGHTS,
) -> float:
    """
    derived_score =
      α * (proofs_replay_stable / max(1, proofs_count))
    + β * continuity_score_avg
    + γ * evidence_integrity_avg
    + δ * authority_chain_strength_avg
    - ε * revoked_proofs

    No proof → no continuity reputation.
    """
    if metrics.proofs_count == 0:
        return 0.0

    stable_ratio = metrics.proofs_replay_stable / max(1, metrics.proofs_count)
    score = (
        weights.alpha * stable_ratio
        + weights.beta * metrics.continuity_score_avg
        + weights.gamma * metrics.evidence_integrity_avg
        + weights.delta * metrics.authority_chain_strength_avg
        - weights.epsilon * metrics.revoked_proofs
    )
    return round(max(0.0, min(1.0, score)), 6)


@dataclass
class ContinuityValidatedReputation:
    """CVR — continuity-validated reputation as a first-class governed object."""

    cvr_id: str
    subject_id: str
    scope: dict[str, Any]
    basis: dict[str, list[str]]
    metrics: ReputationMetrics
    derived_score: float
    law_surfaces: list[str] = field(default_factory=lambda: list(DEFAULT_REPUTATION_LAW_SURFACES))
    last_recomputed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cvr_id": self.cvr_id,
            "subject_id": self.subject_id,
            "scope": dict(self.scope),
            "basis": {key: list(value) for key, value in self.basis.items()},
            "metrics": self.metrics.to_dict(),
            "derived_score": self.derived_score,
            "law_surfaces": list(self.law_surfaces),
            "last_recomputed_at": self.last_recomputed_at,
        }


# Alias for continuity-grade reputation naming in the governance stack.
ContinuityReputation = ContinuityValidatedReputation


def new_cvr_id() -> str:
    return f"cvr:{uuid.uuid4().hex[:16]}"


def compute_reputation_metrics(
    store: CCSStore,
    proofs: list[Proof],
) -> ReputationMetrics:
    metrics = ReputationMetrics()
    metrics.proofs_count = len(proofs)
    if not proofs:
        return metrics

    continuity_scores: list[float] = []
    evidence_scores: list[float] = []
    authority_scores: list[float] = []

    for proof in proofs:
        if proof.status == ProofStatus.REVOKED:
            metrics.revoked_proofs += 1
            continue

        is_valid, _detail = valid_proof(store, proof)
        trace = store.traces.get(proof.continuity_trace_ref)
        if trace is None:
            continue

        replay_fp = continuity_trace_fingerprint(replay_trace_from_store(store, trace))
        if replay_fp == continuity_trace_fingerprint(trace) and is_valid:
            metrics.proofs_replay_stable += 1

        report = evaluate_trace_ugr_invariants(store, trace)
        continuity_scores.append(trace_continuity_score(report))
        evidence_scores.append(trace_evidence_integrity_score(store, trace))
        authority_scores.append(trace_authority_chain_strength(store, trace))

    if continuity_scores:
        metrics.continuity_score_avg = round(sum(continuity_scores) / len(continuity_scores), 6)
    if evidence_scores:
        metrics.evidence_integrity_avg = round(sum(evidence_scores) / len(evidence_scores), 6)
    if authority_scores:
        metrics.authority_chain_strength_avg = round(sum(authority_scores) / len(authority_scores), 6)

    return metrics


def compute_cvr(
    *,
    store: CCSStore,
    subject_id: str,
    proofs: list[Proof],
    scope: dict[str, Any] | None = None,
    domains: list[str] | None = None,
    cvr_id: str | None = None,
    weights: ReputationWeights = DEFAULT_REPUTATION_WEIGHTS,
) -> ContinuityValidatedReputation:
    """Recompute CVR from proof and trace basis. Replay-sensitive and revocation-aware."""
    metrics = compute_reputation_metrics(store, proofs)
    derived = compute_derived_score(metrics, weights=weights)
    proof_refs = [proof.proof_id for proof in proofs]
    trace_refs = sorted({proof.continuity_trace_ref for proof in proofs})
    scope_payload = dict(scope or {})
    if domains:
        scope_payload["domains"] = list(domains)

    return ContinuityValidatedReputation(
        cvr_id=cvr_id or new_cvr_id(),
        subject_id=subject_id,
        scope=scope_payload,
        basis={"proofs": proof_refs, "traces": trace_refs},
        metrics=metrics,
        derived_score=derived,
    )
