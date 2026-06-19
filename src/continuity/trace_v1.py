"""Continuity Reputation v1 — trace projection and metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.continuity.ccs import ContinuityTrace, continuity_trace_fingerprint, law_surface_has_law


def _flatten_law_surfaces(law_surfaces: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("aais_laws", "csleis_laws", "other_laws"):
        for item in law_surfaces.get(key, []) or []:
            refs.append(str(item))
    return sorted(set(refs))


@dataclass(frozen=True)
class ContinuityMetrics:
    """Per-trace continuity metrics referenced by ContinuityTrace v1."""

    metrics_id: str
    continuity_score: float
    lineage_strength: float = 0.0
    authority_chain_strength: float = 0.0
    evidence_integrity_score: float = 0.0
    drift_risk: float = 0.0
    preservation_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics_id": self.metrics_id,
            "continuity_score": self.continuity_score,
            "lineage_strength": self.lineage_strength,
            "authority_chain_strength": self.authority_chain_strength,
            "evidence_integrity_score": self.evidence_integrity_score,
            "drift_risk": self.drift_risk,
            "preservation_risk": self.preservation_risk,
        }


@dataclass(frozen=True)
class ContinuityTraceV1:
    """Formal v1 projection over CCS ContinuityTrace + store refs."""

    trace_id: str
    subject_ref: str
    identity_refs: list[str]
    event_refs: list[str]
    evaluation_refs: list[str]
    evidence_refs: list[str]
    metrics_ref: str
    law_surfaces: list[str]
    trace_hash: str
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "subject_ref": self.subject_ref,
            "identity_refs": list(self.identity_refs),
            "event_refs": list(self.event_refs),
            "evaluation_refs": list(self.evaluation_refs),
            "evidence_refs": list(self.evidence_refs),
            "metrics_ref": self.metrics_ref,
            "law_surfaces": list(self.law_surfaces),
            "trace_hash": self.trace_hash,
            "created_at": self.created_at,
        }


def project_trace_v1(
    trace: ContinuityTrace,
    *,
    subject_ref: str,
    metrics_ref: str = "",
    created_at: str = "",
) -> ContinuityTraceV1:
    """Project a CCS ContinuityTrace into the v1 formal shape."""
    evaluation_refs: set[str] = set()
    evidence_refs: set[str] = set()
    for item in trace.timeline:
        evaluation_refs.update(item.get("evaluations", []))
        evidence_refs.update(item.get("evidence", []))

    return ContinuityTraceV1(
        trace_id=trace.id,
        subject_ref=subject_ref,
        identity_refs=list(trace.scope.get("identity_ids", [])),
        event_refs=list(trace.scope.get("event_ids", [])),
        evaluation_refs=sorted(evaluation_refs),
        evidence_refs=sorted(evidence_refs),
        metrics_ref=metrics_ref,
        law_surfaces=_flatten_law_surfaces(trace.law_surfaces),
        trace_hash=continuity_trace_fingerprint(trace),
        created_at=created_at,
    )


def normalize_evidence_ref(evidence_id: str) -> str:
    """DS-2: canonical evidence reference encoding."""
    return evidence_id.strip().lower()


def denormalize_evidence_ref(normalized: str) -> str:
    """DS-2: reverse of normalize_evidence_ref (identity for canonical IDs)."""
    return normalized


def evidence_ref_roundtrip_stable(evidence_id: str) -> bool:
    return denormalize_evidence_ref(normalize_evidence_ref(evidence_id)) == evidence_id.strip().lower()


def trace_has_required_law_surfaces(trace: ContinuityTrace) -> bool:
    return law_surface_has_law(trace.law_surfaces)
