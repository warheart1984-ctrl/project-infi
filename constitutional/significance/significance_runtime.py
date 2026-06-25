"""Significance Runtime v0 — ranks and audits constitutional artifacts."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.articles import (
    ARTICLE_Q_REFERENCE,
    SIGNIFICANCE_CORE_CAPACITY,
    SIGNIFICANCE_INVARIANT,
)
from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.artifact_index import ArtifactIndex, CORE_TIERS, get_artifact_index
from constitutional.significance.significance_failures import (
    QF_SURFACE_COUNT,
    SignificanceFailureClass as QF,
    qf_surface_code,
)

SIGNIFICANCE_STATE_ID = "significance__global"
SIGNIFICANCE_RUNTIME_NAME = "SignificanceRuntime"


class SignificanceAuditState(BaseModel):
    """Global significance lattice audit (Article Q)."""

    state_id: str = SIGNIFICANCE_STATE_ID
    state_type: str = "significance"
    snapshot_at: datetime
    version: int = Field(ge=1)

    significance_health_index: float = Field(ge=0.0, le=1.0)
    failed_surfaces: list[QF] = Field(default_factory=list)

    unranked_artifacts: list[str] = Field(default_factory=list)
    suspected_misranked_artifacts: list[str] = Field(default_factory=list)
    tier_bloat_tiers: list[int] = Field(default_factory=list)
    priority_inversions: list[str] = Field(default_factory=list)


def load_significance_audit_state(csr: ConstitutionalStateRuntime) -> SignificanceAuditState:
    doc = csr.get_domain_doc(SIGNIFICANCE_STATE_ID, SignificanceAuditState)
    assert isinstance(doc, SignificanceAuditState)
    return doc


class SignificanceRuntime:
    """Audits what remains unranked, mis-ranked, or bloated."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        artifact_index: ArtifactIndex | None = None,
        core_capacity: int = SIGNIFICANCE_CORE_CAPACITY,
    ) -> None:
        self.csr = csr
        self.artifact_index = artifact_index or get_artifact_index(csr)
        self.core_capacity = core_capacity

    def run_scan(self, snapshot_at: datetime | None = None) -> SignificanceAuditState:
        now = snapshot_at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        failed: list[QF] = []
        unranked: list[str] = []
        misranked: list[str] = []
        bloat_tiers: list[int] = []
        inversions: list[str] = []

        for artifact in self.artifact_index.all():
            if artifact.significance_tier is None:
                failed.append(QF.UNRANKED_CORE)
                unranked.append(artifact.id)

        core = [
            artifact
            for artifact in self.artifact_index.all()
            if artifact.significance_tier in CORE_TIERS
        ]
        if not core:
            if QF.UNRANKED_CORE not in failed:
                failed.append(QF.UNRANKED_CORE)

        if len(core) > self.core_capacity:
            failed.append(QF.TIER_BLOAT)
            bloat_tiers.extend([0, 1])

        for artifact in core:
            if not artifact.significance_rationale:
                failed.append(QF.SIGNIFICANCE_AMNESIA)
                misranked.append(artifact.id)

        inversions = self._detect_priority_inversions()
        if inversions:
            failed.append(QF.PRIORITY_INVERSION)

        failed = list(dict.fromkeys(failed))
        significance_health_index = max(0.0, 1.0 - len(failed) / float(QF_SURFACE_COUNT))

        try:
            prev = load_significance_audit_state(self.csr)
            version = prev.version + 1
        except KeyError:
            version = 1

        state = SignificanceAuditState(
            snapshot_at=now,
            version=version,
            significance_health_index=significance_health_index,
            failed_surfaces=failed,
            unranked_artifacts=unranked,
            suspected_misranked_artifacts=misranked,
            tier_bloat_tiers=list(dict.fromkeys(bloat_tiers)),
            priority_inversions=inversions,
        )

        self.csr.register_or_replace_state(
            StateObject(
                state_id=SIGNIFICANCE_STATE_ID,
                state_type="significance",
                current_state="Observed",
            )
        )
        self.csr.put_domain_doc(SIGNIFICANCE_STATE_ID, "significance", state)
        return state

    def _detect_priority_inversions(self) -> list[str]:
        inversions: list[str] = []
        for artifact in self.artifact_index.all():
            if not artifact.overrides_core:
                continue
            if artifact.significance_tier is not None and artifact.significance_tier >= 3:
                inversions.append(artifact.id)
                continue
            if artifact.artifact_type == "decision" and artifact.significance_tier in (3, 4):
                inversions.append(artifact.id)
        return inversions
