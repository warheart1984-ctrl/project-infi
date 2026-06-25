"""VAS-1 — Validation After Surpassment (three-stage formal protocol)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.continuity.ra.models import ValidationContext
from src.continuity.ra.spec import VAS1_CRITERIA, VAS1_MIN_CRITERIA_PASSED, VAS1_REFERENCE


class SurpassmentCandidate(BaseModel):
    """Stage 1 — SSDE-1 trigger: candidate surpassment, not yet validated."""

    insight_id: str
    explanatory_gain: float = 0.0
    integrates_primitives: list[str] = Field(default_factory=list)
    resolves_founder_limitation: bool = False
    survives_critique: bool = False
    accumulation_signature: str = "NONE"

    @property
    def stage_met(self) -> bool:
        has_gain = self.explanatory_gain > 0
        has_integration = len(self.integrates_primitives) >= 2
        has_signature = self.accumulation_signature in ("A3", "A4")
        return (
            (has_gain or has_signature)
            and has_integration
            and self.resolves_founder_limitation
            and self.survives_critique
        )


class AcceptanceEvent(BaseModel):
    """Stage 2 — FAP-1 trigger: lineage acceptance, not validation."""

    acknowledged_superiority: bool = False
    integrated_into_grammar: bool = False
    updated_invariants: bool = False
    relinquished_authority: bool = False

    @property
    def stage_met(self) -> bool:
        return (
            self.acknowledged_superiority
            and self.integrated_into_grammar
            and self.updated_invariants
            and self.relinquished_authority
        )


class VAS1Result(BaseModel):
    """Stage 3 — reality validation proper."""

    reference: str = VAS1_REFERENCE
    passed: bool = False
    criteria_passed: list[str] = Field(default_factory=list)
    criteria_failed: list[str] = Field(default_factory=list)
    reality_veto: bool = False


class VAS1ProtocolResult(BaseModel):
    """Full VAS-1 protocol: surpassment → acceptance → reality validation."""

    reference: str = VAS1_REFERENCE
    stage1_surpassment: SurpassmentCandidate
    stage2_acceptance: AcceptanceEvent
    stage3_validation: VAS1Result
    surpassment_is_candidate_only: bool = True
    acceptance_is_not_validation: bool = True
    validated: bool = False
    blockers: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def validate_change_vas1(ctx: ValidationContext) -> VAS1Result:
    """
    Stage 3 — Reality Validation (VAS-1 proper).

    At least 3 of 5 criteria must pass. This is the reality veto:
    surpassment and acceptance alone never finalize an improvement.
    """
    criteria: list[tuple[str, bool]] = [
        ("predictiveAccuracy", ctx.predictive_accuracy_delta > 0),
        ("explanatoryCompression", ctx.explanatory_compression_delta > 0),
        ("crossDomainConvergence", ctx.cross_domain_convergence >= 0.5),
        ("operationalOutcome", ctx.operational_outcome_delta > 0),
        ("critiqueStability", ctx.critique_stability >= 0.5),
    ]

    passed_names = [name for name, ok in criteria if ok]
    failed_names = [name for name, ok in criteria if not ok]
    passed = len(passed_names) >= VAS1_MIN_CRITERIA_PASSED

    return VAS1Result(
        passed=passed,
        criteria_passed=passed_names,
        criteria_failed=failed_names,
        reality_veto=not passed,
    )


def run_vas1_protocol(
    surpassment: SurpassmentCandidate,
    acceptance: AcceptanceEvent,
    validation_ctx: ValidationContext,
) -> VAS1ProtocolResult:
    """
    VAS-1 formal protocol:
    Stage 1 (SSDE) → Stage 2 (FAP) → Stage 3 (reality).

    Surpassment is not validation. Acceptance is not validation. Only reality validates.
    """
    blockers: list[str] = []
    notes: list[str] = [
        "Surpassment is not validation.",
        "Acceptance is not validation.",
        "Only reality can validate.",
    ]

    if not surpassment.stage_met:
        blockers.append("Stage 1: no qualifying surpassment candidate (SSDE-1).")
    if not acceptance.stage_met:
        blockers.append("Stage 2: lineage has not completed acceptance (FAP-1).")

    validation = validate_change_vas1(validation_ctx)
    if validation.reality_veto:
        blockers.append(
            f"Stage 3: reality veto — fewer than {VAS1_MIN_CRITERIA_PASSED} validation criteria passed."
        )

    validated = surpassment.stage_met and acceptance.stage_met and validation.passed
    if validated:
        notes.append("Improvement validated by consequences (≥3 VAS-1 criteria).")
    elif acceptance.stage_met and not validation.passed:
        notes.append("Accepted improvement rejected by reality — acceptance does not override VAS-1.")

    return VAS1ProtocolResult(
        stage1_surpassment=surpassment,
        stage2_acceptance=acceptance,
        stage3_validation=validation,
        validated=validated,
        blockers=blockers,
        notes=notes,
    )


def format_vas1_criteria() -> str:
    lines = [f"=== {VAS1_REFERENCE} — Validation Criteria ===", ""]
    for key, description in VAS1_CRITERIA:
        lines.append(f"  {key}: {description}")
    lines.append("")
    lines.append(f"Pass threshold: ≥ {VAS1_MIN_CRITERIA_PASSED} of 5 criteria.")
    return "\n".join(lines)
