"""Significance Stability Runtime — falsification engine for tier drift (Article Q-2)."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_Q2_REFERENCE,
    PURPOSE_CONTINUITY_INVARIANT,
    SIGNIFICANCE_STABILITY_INVARIANT,
)
from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.artifact_index import ArtifactIndex, CORE_TIERS, get_artifact_index
from constitutional.significance.significance_failures import SignificanceFailureClass as QF

SIGNIFICANCE_STABILITY_STATE_ID = "significance_stability__global"
SIGNIFICANCE_STABILITY_RUNTIME_NAME = "SignificanceStabilityRuntime"


class SignificanceStabilityState(BaseModel):
    state_id: str = SIGNIFICANCE_STABILITY_STATE_ID
    state_type: str = "significance_stability"
    snapshot_at: datetime
    version: int = Field(ge=1)

    stability_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[QF] = Field(default_factory=list)
    unjustified_changes: list[str] = Field(default_factory=list)
    drift_candidates: list[str] = Field(default_factory=list)


def load_significance_stability_state(csr: ConstitutionalStateRuntime) -> SignificanceStabilityState:
    doc = csr.get_domain_doc(SIGNIFICANCE_STABILITY_STATE_ID, SignificanceStabilityState)
    assert isinstance(doc, SignificanceStabilityState)
    return doc


class SignificanceStabilityRuntime:
    """Detects significance drift — tier changes without constitutional justification."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        artifact_index: ArtifactIndex | None = None,
    ) -> None:
        self.csr = csr
        self.artifact_index = artifact_index or get_artifact_index(csr)

    def run(self, snapshot_at: datetime | None = None) -> SignificanceStabilityState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[QF] = []
        drift_candidates: list[str] = []
        unjustified_changes: list[str] = []

        for artifact in self.artifact_index.all():
            prev = artifact.previous_tier
            curr = artifact.significance_tier
            if prev is None or curr is None:
                continue
            if prev == curr:
                continue

            if not artifact.significance_change_rationale:
                failed.append(QF.SIGNIFICANCE_DRIFT)
                unjustified_changes.append(artifact.id)
            elif self._contradicts_purpose(artifact):
                failed.append(QF.SIGNIFICANCE_DRIFT)
                drift_candidates.append(artifact.id)

        failed = list(dict.fromkeys(failed))
        stability_index = 1.0 if not failed else 0.0

        try:
            prev_state = load_significance_stability_state(self.csr)
            version = prev_state.version + 1
        except KeyError:
            version = 1

        state = SignificanceStabilityState(
            snapshot_at=now,
            version=version,
            stability_index=stability_index,
            failed_surfaces=failed,
            unjustified_changes=unjustified_changes,
            drift_candidates=drift_candidates,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=SIGNIFICANCE_STABILITY_STATE_ID,
                state_type="significance_stability",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(SIGNIFICANCE_STABILITY_STATE_ID, "significance_stability", state)
        return state

    def _contradicts_purpose(self, artifact) -> bool:
        """Heuristic: lowering a core-tier artifact without purpose-linked rationale."""
        if artifact.previous_tier not in CORE_TIERS:
            return False
        if artifact.significance_tier is None:
            return True
        if artifact.significance_tier > artifact.previous_tier:
            rationale = (artifact.significance_change_rationale or "").lower()
            purpose_tokens = ("purpose", "mission", "invariant", PURPOSE_CONTINUITY_INVARIANT.lower())
            return not any(token in rationale for token in purpose_tokens)
        return False
