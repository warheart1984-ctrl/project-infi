"""Context-aware significance evolution test."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from constitutional.significance.artifact_index import ArtifactIndex, get_artifact_index
from constitutional.significance.stewardship_context_ledger import StewardshipContextLedger
from constitutional.runtime.runtime import ConstitutionalStateRuntime


class ContextAwareSignificanceEvolutionResult(BaseModel):
    passed: bool
    evolution_index: float = Field(ge=0.0, le=1.0)
    obsolete: list[str] = Field(default_factory=list)
    stasis: list[str] = Field(default_factory=list)
    context_misalignment: list[str] = Field(default_factory=list)


class ContextAwareSignificanceEvolutionTest:
    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        artifact_index: ArtifactIndex | None = None,
        context_ledger: StewardshipContextLedger,
        current_env_snapshot: dict[str, Any],
    ) -> None:
        self.csr = csr
        self.artifact_index = artifact_index or get_artifact_index(csr)
        self.context_ledger = context_ledger
        self.current_env_snapshot = current_env_snapshot

    def run(self) -> ContextAwareSignificanceEvolutionResult:
        obsolete: list[str] = []
        stasis: list[str] = []
        misaligned: list[str] = []

        for artifact in self.artifact_index.all_significant():
            ctx_entries = self.context_ledger.entries_for_artifact(artifact.id)
            if not ctx_entries:
                continue

            last_ctx = ctx_entries[-1]
            if self._environment_changed(last_ctx.environmental_factors, self.current_env_snapshot):
                if not artifact.pending_reclassification:
                    stasis.append(artifact.id)

            if self._calibration_misaligned(last_ctx, self.current_env_snapshot):
                misaligned.append(artifact.id)

        failures = len(set(obsolete + stasis + misaligned))
        significant_count = max(1, len(self.artifact_index.all_significant()))
        evolution_index = 1.0 - (failures / float(significant_count))
        passed = evolution_index >= 0.8

        return ContextAwareSignificanceEvolutionResult(
            passed=passed,
            evolution_index=evolution_index,
            obsolete=obsolete,
            stasis=stasis,
            context_misalignment=misaligned,
        )

    def _environment_changed(
        self,
        historical_factors: list[str],
        current_env_snapshot: dict[str, Any],
    ) -> bool:
        if not historical_factors:
            return False
        current_tags = set(current_env_snapshot.get("environmental_factors", []))
        return bool(current_tags) and not current_tags.intersection(historical_factors)

    def _calibration_misaligned(self, ctx_entry, current_env_snapshot: dict[str, Any]) -> bool:
        current_risks = set(current_env_snapshot.get("risks_salient", []))
        if not current_risks or not ctx_entry.risks_salient:
            return False
        return len(current_risks.intersection(ctx_entry.risks_salient)) == 0
