"""Significance Review Runtime — continuity of tier assignments across stewards."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.articles import SUCCESSION_MIN_SIGNIFICANCE_CONTINUITY
from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.artifact_index import ArtifactIndex, get_artifact_index
from constitutional.significance.reference_lattice import get_reference_lattice
from constitutional.significance.significance_judgment_runtime import (
    load_significance_judgment_state,
)

SIGNIFICANCE_REVIEW_STATE_ID = "significance_review__global"


class SignificanceReviewState(BaseModel):
    state_id: str = SIGNIFICANCE_REVIEW_STATE_ID
    state_type: str = "significance_review"
    snapshot_at: datetime
    version: int = Field(ge=1)

    continuity_index: float = Field(ge=0.0, le=1.0)
    aligned_artifacts: list[str] = Field(default_factory=list)
    misaligned_artifacts: list[str] = Field(default_factory=list)
    missing_rationale: list[str] = Field(default_factory=list)


def load_significance_review_state(csr: ConstitutionalStateRuntime) -> SignificanceReviewState:
    doc = csr.get_domain_doc(SIGNIFICANCE_REVIEW_STATE_ID, SignificanceReviewState)
    assert isinstance(doc, SignificanceReviewState)
    return doc


class SignificanceReviewRuntime:
    """Compares steward judgments and lattice assignments for continuity."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        artifact_index: ArtifactIndex | None = None,
        steward_knowledge_index: dict[str, str] | None = None,
    ) -> None:
        self.csr = csr
        self.artifact_index = artifact_index or get_artifact_index(csr)
        self.steward_knowledge_index = steward_knowledge_index or {}

    def run_review(self, snapshot_at: datetime | None = None) -> SignificanceReviewState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        reference = get_reference_lattice()
        judgment = load_significance_judgment_state(self.csr)

        aligned: list[str] = []
        misaligned: list[str] = []
        missing_rationale: list[str] = []

        for artifact_id, ref_tier in reference.items():
            artifact = self.artifact_index.get(artifact_id)
            if artifact is None:
                continue
            if not artifact.significance_rationale:
                missing_rationale.append(artifact_id)
            if judgment and artifact_id in judgment.steward_answers:
                answer = judgment.steward_answers[artifact_id]
                if answer.tier == ref_tier or (
                    artifact.significance_tier is not None and artifact.significance_tier == answer.tier
                ):
                    aligned.append(artifact_id)
                else:
                    misaligned.append(artifact_id)
            elif artifact.significance_tier == ref_tier:
                aligned.append(artifact_id)
            else:
                misaligned.append(artifact_id)

        total = len(reference) or 1
        continuity_index = len(aligned) / float(total)
        if missing_rationale:
            continuity_index = min(continuity_index, SUCCESSION_MIN_SIGNIFICANCE_CONTINUITY - 0.01)

        try:
            prev = load_significance_review_state(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = SignificanceReviewState(
            snapshot_at=now,
            version=version,
            continuity_index=continuity_index,
            aligned_artifacts=aligned,
            misaligned_artifacts=misaligned,
            missing_rationale=missing_rationale,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=SIGNIFICANCE_REVIEW_STATE_ID,
                state_type="significance_review",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(SIGNIFICANCE_REVIEW_STATE_ID, "significance_review", state)
        return state
