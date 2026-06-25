"""JPSS Steward Competency Model — skill stack for judgment-preserving stewards."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from constitutional.eck2.runtime import load_eck2_pipeline
from constitutional.jpss.drift import detect_jpss_drift
from constitutional.jpss.runtime import load_jpss_cycle
from constitutional.runtime.runtime import ConstitutionalStateRuntime

StewardCompetencyDomain = Literal[
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome_reflection",
    "prior",
    "reconstruction",
]

STEWARD_COMPETENCY_DOMAINS: tuple[StewardCompetencyDomain, ...] = (
    "environment",
    "perception",
    "salience",
    "calibration",
    "decision",
    "outcome_reflection",
    "prior",
    "reconstruction",
)

STEWARD_COMPETENCY_SKILLS: dict[StewardCompetencyDomain, tuple[str, ...]] = {
    "environment": (
        "Context reconstruction",
        "Context discrimination",
    ),
    "perception": (
        "Signal literacy",
        "Channel awareness",
    ),
    "salience": (
        "Attention mapping",
        "Bias recognition",
    ),
    "calibration": (
        "Threshold reasoning",
        "Risk tolerance articulation",
    ),
    "decision": (
        "Invariant application",
        "Option evaluation",
    ),
    "outcome_reflection": (
        "Outcome tracing",
        "Reflective learning",
    ),
    "prior": (
        "Prior surfacing",
        "Prior revision",
    ),
    "reconstruction": (
        "Historical judgment reconstruction",
        "Drift detection",
    ),
}

STEWARD_COMPETENCY_PASS_THRESHOLD = 0.75


class StewardCompetencyScore(BaseModel):
    domain: StewardCompetencyDomain
    skills: list[str] = Field(default_factory=list)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool = False
    evidence: list[str] = Field(default_factory=list)


class StewardCompetencyAssessment(BaseModel):
    steward_id: str = "steward"
    domain_scores: list[StewardCompetencyScore] = Field(default_factory=list)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = False
    dual_pipeline_demonstrated: bool = False

    @property
    def failed_domains(self) -> list[StewardCompetencyDomain]:
        return [score.domain for score in self.domain_scores if not score.passed]


def assess_steward_competency(
    csr: ConstitutionalStateRuntime,
    *,
    steward_id: str = "steward",
) -> StewardCompetencyAssessment:
    """Assess JPSS competency from preserved registers and dual-pipeline artifacts."""
    cycle = load_jpss_cycle(csr)
    pipeline = load_eck2_pipeline(csr)
    drift = detect_jpss_drift(csr, decision_id=cycle.decision_id if cycle else None, cycle=cycle)

    scores: list[StewardCompetencyScore] = []

    env_score = 1.0 if cycle and cycle.environment.constraints_active else 0.0
    scores.append(
        StewardCompetencyScore(
            domain="environment",
            skills=list(STEWARD_COMPETENCY_SKILLS["environment"]),
            score=env_score,
            passed=env_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["environment register populated"] if env_score else ["missing environment anchor"],
        )
    )

    perception_score = 1.0 if cycle and cycle.perception.available_signals else 0.0
    scores.append(
        StewardCompetencyScore(
            domain="perception",
            skills=list(STEWARD_COMPETENCY_SKILLS["perception"]),
            score=perception_score,
            passed=perception_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["perception signals recorded"] if perception_score else ["no perception signals"],
        )
    )

    salience_score = 1.0 if cycle and cycle.salience.primary_signals else 0.0
    scores.append(
        StewardCompetencyScore(
            domain="salience",
            skills=list(STEWARD_COMPETENCY_SKILLS["salience"]),
            score=salience_score,
            passed=salience_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["salience mapping recorded"] if salience_score else ["salience not explicit"],
        )
    )

    calibration_score = 1.0 if cycle and cycle.calibration.evidence_threshold is not None else 0.0
    scores.append(
        StewardCompetencyScore(
            domain="calibration",
            skills=list(STEWARD_COMPETENCY_SKILLS["calibration"]),
            score=calibration_score,
            passed=calibration_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["calibration thresholds recorded"] if calibration_score else ["calibration missing"],
        )
    )

    decision_score = 1.0 if cycle and cycle.decision.rationale else 0.0
    scores.append(
        StewardCompetencyScore(
            domain="decision",
            skills=list(STEWARD_COMPETENCY_SKILLS["decision"]),
            score=decision_score,
            passed=decision_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["decision rationale recorded"] if decision_score else ["decision rationale missing"],
        )
    )

    outcome_reflection_score = (
        1.0 if cycle and cycle.outcome.observed_result and cycle.reflection.lessons else 0.0
    )
    scores.append(
        StewardCompetencyScore(
            domain="outcome_reflection",
            skills=list(STEWARD_COMPETENCY_SKILLS["outcome_reflection"]),
            score=outcome_reflection_score,
            passed=outcome_reflection_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["outcome and reflection linked"] if outcome_reflection_score else ["reflection gap"],
        )
    )

    prior_score = 1.0 if cycle and cycle.perception.available_signals else 0.0
    if drift.active_drifts:
        prior_score = max(0.0, prior_score - 0.25)
    scores.append(
        StewardCompetencyScore(
            domain="prior",
            skills=list(STEWARD_COMPETENCY_SKILLS["prior"]),
            score=prior_score,
            passed=prior_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["priors implied from perception ledger"] if prior_score else ["prior drift risk"],
        )
    )

    dual_pipeline = bool(
        pipeline
        and pipeline.reconstruction.reconstructable
        and pipeline.drift_symmetry.symmetric
    )
    reconstruction_score = 1.0 if dual_pipeline else (0.5 if pipeline else 0.0)
    scores.append(
        StewardCompetencyScore(
            domain="reconstruction",
            skills=list(STEWARD_COMPETENCY_SKILLS["reconstruction"]),
            score=reconstruction_score,
            passed=reconstruction_score >= STEWARD_COMPETENCY_PASS_THRESHOLD,
            evidence=["ECK-R reconstruction verified"] if dual_pipeline else ["reconstruction incomplete"],
        )
    )

    overall = sum(score.score for score in scores) / len(scores) if scores else 0.0
    passed = overall >= STEWARD_COMPETENCY_PASS_THRESHOLD and dual_pipeline

    return StewardCompetencyAssessment(
        steward_id=steward_id,
        domain_scores=scores,
        overall_score=round(overall, 4),
        passed=passed,
        dual_pipeline_demonstrated=dual_pipeline,
    )


def format_competency_model() -> str:
    lines = [
        "=== JPSS Steward Competency Model ===",
        "",
        "A steward passes JPSS competency when they can run both formation and",
        "reconstruction cycles consciously and explicitly, not just intuitively.",
        "",
    ]
    for domain in STEWARD_COMPETENCY_DOMAINS:
        title = domain.replace("_", " ").title()
        lines.append(title)
        for skill in STEWARD_COMPETENCY_SKILLS[domain]:
            lines.append(f"  - {skill}")
        lines.append("")
    return "\n".join(lines).strip()
