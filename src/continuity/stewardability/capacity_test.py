"""Stewardship Capacity Test — can this person regenerate the stack from first principles?"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.stewardability.register import LineageImpact

REGENERATION_LAYERS: tuple[str, ...] = (
    "purpose",
    "identity",
    "invariants",
    "constitutional_logic",
    "legitimacy_logic",
    "lineage_logic",
)

DRIFT_SURFACES: tuple[str, ...] = (
    "adaptive_drift",
    "invariant_drift",
    "constitutional_drift",
    "authority_drift",
    "recognition_drift",
    "lineage_drift",
    "meta_steward_drift",
)

SectionStatus = Literal["PASS", "FAIL"]


class RegenerationSubmission(BaseModel):
    """Candidate regenerates continuity layers from first principles."""

    reconstructions: dict[str, str] = Field(default_factory=dict)


class DriftDetectionSubmission(BaseModel):
    """Candidate detects drift in own, historical, and hypothetical systems."""

    own_system_findings: list[str] = Field(default_factory=list)
    historical_findings: list[str] = Field(default_factory=list)
    hypothetical_findings: list[str] = Field(default_factory=list)


class PrincipledDisagreementSubmission(BaseModel):
    """Candidate disagrees with founders while preserving identity."""

    founder_critiques: list[str] = Field(default_factory=list)
    invariant_critiques: list[str] = Field(default_factory=list)
    constitutional_critiques: list[str] = Field(default_factory=list)
    lineage_critiques: list[str] = Field(default_factory=list)
    lineage_impact: LineageImpact = "UNCHANGED"
    strengthens_continuity: bool = False


class CapacityTestSectionResult(BaseModel):
    section: Literal["regeneration", "drift_detection", "principled_disagreement"]
    status: SectionStatus
    score: float = Field(ge=0.0, le=1.0)
    blockers: list[str] = Field(default_factory=list)


class StewardshipCapacityTestInput(BaseModel):
    candidate_id: str
    regeneration: RegenerationSubmission = Field(default_factory=RegenerationSubmission)
    drift_detection: DriftDetectionSubmission = Field(default_factory=DriftDetectionSubmission)
    principled_disagreement: PrincipledDisagreementSubmission = Field(
        default_factory=PrincipledDisagreementSubmission
    )


class StewardshipCapacityTestResult(BaseModel):
    candidate_id: str
    evaluated_at: datetime
    passed: bool
    capacity_index: float = Field(ge=0.0, le=1.0)
    sections: list[CapacityTestSectionResult] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)


def _evaluate_regeneration(submission: RegenerationSubmission) -> CapacityTestSectionResult:
    blockers: list[str] = []
    met = [layer for layer in REGENERATION_LAYERS if layer in submission.reconstructions and submission.reconstructions[layer].strip()]
    missing = [layer for layer in REGENERATION_LAYERS if layer not in met]
    score = len(met) / len(REGENERATION_LAYERS) if REGENERATION_LAYERS else 1.0
    if missing:
        blockers.append(f"Missing regeneration for: {', '.join(missing)}")
    status: SectionStatus = "PASS" if score >= 0.85 else "FAIL"
    return CapacityTestSectionResult(
        section="regeneration",
        status=status,
        score=score,
        blockers=blockers,
    )


def _evaluate_drift_detection(submission: DriftDetectionSubmission) -> CapacityTestSectionResult:
    blockers: list[str] = []
    checks = [
        ("own regenerated system", submission.own_system_findings),
        ("historical system", submission.historical_findings),
        ("hypothetical future system", submission.hypothetical_findings),
    ]
    passed_checks = sum(1 for _, findings in checks if findings)
    score = passed_checks / len(checks)
    for label, findings in checks:
        if not findings:
            blockers.append(f"No drift detected in {label}.")
    status: SectionStatus = "PASS" if score >= 1.0 else "FAIL"
    return CapacityTestSectionResult(
        section="drift_detection",
        status=status,
        score=score,
        blockers=blockers,
    )


def _evaluate_principled_disagreement(submission: PrincipledDisagreementSubmission) -> CapacityTestSectionResult:
    blockers: list[str] = []
    critique_count = (
        len(submission.founder_critiques)
        + len(submission.invariant_critiques)
        + len(submission.constitutional_critiques)
        + len(submission.lineage_critiques)
    )
    if critique_count == 0:
        blockers.append("No principled disagreement demonstrated.")
    if submission.lineage_impact not in {"STRENGTHENED", "UNCHANGED"}:
        blockers.append("Disagreement weakened lineage.")
    if not submission.strengthens_continuity and submission.lineage_impact != "STRENGTHENED":
        blockers.append("Disagreement did not strengthen continuity.")

    score_parts = [
        1.0 if critique_count > 0 else 0.0,
        1.0 if submission.lineage_impact in {"STRENGTHENED", "UNCHANGED"} else 0.0,
        1.0 if submission.strengthens_continuity or submission.lineage_impact == "STRENGTHENED" else 0.0,
    ]
    score = sum(score_parts) / len(score_parts)
    status: SectionStatus = "PASS" if score >= 0.85 and critique_count > 0 else "FAIL"
    return CapacityTestSectionResult(
        section="principled_disagreement",
        status=status,
        score=score,
        blockers=blockers,
    )


def run_stewardship_capacity_test(test_input: StewardshipCapacityTestInput) -> StewardshipCapacityTestResult:
    """Run the corrected three-section Stewardship Capacity Test."""
    sections = [
        _evaluate_regeneration(test_input.regeneration),
        _evaluate_drift_detection(test_input.drift_detection),
        _evaluate_principled_disagreement(test_input.principled_disagreement),
    ]
    blockers = [blocker for section in sections for blocker in section.blockers]
    capacity_index = sum(section.score for section in sections) / len(sections)
    passed = all(section.status == "PASS" for section in sections)

    return StewardshipCapacityTestResult(
        candidate_id=test_input.candidate_id,
        evaluated_at=datetime.now(UTC).replace(microsecond=0),
        passed=passed,
        capacity_index=capacity_index,
        sections=sections,
        blockers=blockers,
    )


def passing_capacity_test_input(candidate_id: str) -> StewardshipCapacityTestInput:
    """Reference input satisfying all three sections."""
    return StewardshipCapacityTestInput(
        candidate_id=candidate_id,
        regeneration=RegenerationSubmission(
            reconstructions={layer: f"regenerated {layer}" for layer in REGENERATION_LAYERS}
        ),
        drift_detection=DriftDetectionSubmission(
            own_system_findings=["boundary misclassification in regenerated invariants"],
            historical_findings=["calibration drift in prior JPSS cycle"],
            hypothetical_findings=["recognition gatekeeping under low plurality"],
        ),
        principled_disagreement=PrincipledDisagreementSubmission(
            founder_critiques=["founder over-sacralized adaptive signal X"],
            invariant_critiques=["invariant Y should be retired — context changed"],
            constitutional_critiques=["elevation threshold too permissive"],
            lineage_critiques=["lineage narrative omitted failure-driven updates"],
            lineage_impact="STRENGTHENED",
            strengthens_continuity=True,
        ),
    )
