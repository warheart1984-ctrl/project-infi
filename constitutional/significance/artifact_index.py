"""Constitutional artifact index — all rankable artifacts in the CSR."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.runtime.runtime_charter import RUNTIME_CHARTER
from constitutional.significance.reference_lattice import (
    SYNTHETIC_ARTIFACTS,
    get_reference_lattice,
    get_reference_rationales,
)
from constitutional.significance.significance_judgment_runtime import (
    SIGNIFICANCE_JUDGMENT_STATE_ID,
    SignificanceJudgmentState,
    load_significance_judgment_state,
)
from constitutional.significance.significance_tier_register import (
    SignificanceTierRegister,
    load_significance_tier_register,
)

CORE_TIERS = frozenset({0, 1})


class ConstitutionalArtifact(BaseModel):
    """A rankable constitutional artifact."""

    id: str
    artifact_type: str
    title: str = ""
    significance_tier: int | None = None
    previous_tier: int | None = None
    significance_rationale: str | None = None
    significance_change_rationale: str | None = None
    pending_reclassification: bool = False
    overrides_core: bool = False


class ArtifactIndex:
    """Index of all artifacts subject to significance ranking."""

    def __init__(self, artifacts: list[ConstitutionalArtifact]) -> None:
        self._artifacts = {artifact.id: artifact for artifact in artifacts}

    def all(self) -> list[ConstitutionalArtifact]:
        return list(self._artifacts.values())

    def all_significant(self) -> list[ConstitutionalArtifact]:
        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.significance_tier is not None and artifact.significance_tier <= 2
        ]

    def get(self, artifact_id: str) -> ConstitutionalArtifact | None:
        return self._artifacts.get(artifact_id)


def _tier_from_judgment(
    artifact_id: str,
    judgment: SignificanceJudgmentState | None,
) -> tuple[int | None, str | None]:
    if judgment is None:
        return None, None
    answer = judgment.steward_answers.get(artifact_id)
    if answer is None:
        return None, None
    return answer.tier, answer.rationale


def build_artifact_index(
    csr: ConstitutionalStateRuntime,
    *,
    tier_register: SignificanceTierRegister | None = None,
) -> ArtifactIndex:
    """Build artifact index from CSR invariants, runtimes, states, and judgments."""
    register = tier_register or load_significance_tier_register(csr)
    judgment = load_significance_judgment_state(csr)
    reference_lattice = get_reference_lattice()
    reference_rationales = get_reference_rationales()

    artifacts: list[ConstitutionalArtifact] = []

    for name, description in csr.invariant_registry.items():
        record = register.records.get(f"invariant:{name}")
        tier = record.current_tier if record else (0 if name.startswith("CRITICAL_") else 1)
        artifacts.append(
            ConstitutionalArtifact(
                id=f"invariant:{name}",
                artifact_type="invariant",
                title=name,
                significance_tier=tier,
                previous_tier=record.previous_tier if record else None,
                significance_rationale=record.rationale if record else description,
                significance_change_rationale=record.change_rationale if record else None,
                pending_reclassification=record.pending_reclassification if record else False,
            )
        )

    for runtime_name in RUNTIME_CHARTER:
        record = register.records.get(f"runtime:{runtime_name}")
        artifacts.append(
            ConstitutionalArtifact(
                id=f"runtime:{runtime_name}",
                artifact_type="runtime",
                title=runtime_name,
                significance_tier=record.current_tier if record else 1,
                previous_tier=record.previous_tier if record else None,
                significance_rationale=record.rationale if record else f"Resists {RUNTIME_CHARTER[runtime_name][0].value}",
                significance_change_rationale=record.change_rationale if record else None,
                pending_reclassification=record.pending_reclassification if record else False,
            )
        )

    for state in csr.all_states():
        record = register.records.get(f"state:{state.state_id}")
        artifacts.append(
            ConstitutionalArtifact(
                id=f"state:{state.state_id}",
                artifact_type="state",
                title=state.state_id,
                significance_tier=record.current_tier if record else None,
                previous_tier=record.previous_tier if record else None,
                significance_rationale=record.rationale if record else None,
                significance_change_rationale=record.change_rationale if record else None,
                pending_reclassification=record.pending_reclassification if record else False,
            )
        )

    for artifact_id, meta in SYNTHETIC_ARTIFACTS.items():
        ref_tier = reference_lattice.get(artifact_id)
        ref_rat = reference_rationales.get(artifact_id)
        judged_tier, judged_rationale = _tier_from_judgment(artifact_id, judgment)
        record = register.records.get(artifact_id)
        artifacts.append(
            ConstitutionalArtifact(
                id=artifact_id,
                artifact_type="synthetic",
                title=meta.get("title", artifact_id),
                significance_tier=judged_tier if judged_tier is not None else ref_tier,
                previous_tier=record.previous_tier if record else None,
                significance_rationale=judged_rationale or (ref_rat.summary if ref_rat else None),
                significance_change_rationale=record.change_rationale if record else None,
                pending_reclassification=record.pending_reclassification if record else False,
            )
        )

    for receipt in csr.get_all_receipts():
        if receipt.lifecycle.stage != "decision":
            continue
        record = register.records.get(f"decision:{receipt.receipt_id}")
        boundary = receipt.impact_boundary
        overrides = bool(boundary.scope_out and "core" in " ".join(boundary.scope_out).lower())
        artifacts.append(
            ConstitutionalArtifact(
                id=f"decision:{receipt.receipt_id}",
                artifact_type="decision",
                title=receipt.receipt_id,
                significance_tier=record.current_tier if record else 2,
                previous_tier=record.previous_tier if record else None,
                significance_rationale=record.rationale if record else receipt.outputs.notes,
                significance_change_rationale=record.change_rationale if record else None,
                pending_reclassification=record.pending_reclassification if record else False,
                overrides_core=overrides,
            )
        )

    return ArtifactIndex(artifacts)


def get_artifact_index(csr: ConstitutionalStateRuntime) -> ArtifactIndex:
    return build_artifact_index(csr)
