"""Invariant Selection Engine — constitutional classifier for elevation decisions."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.jpss.constitutional_ledgers import (
    ElevationReviewEntry,
    InvariantCandidateEntry,
    load_elevation_review_ledger,
    load_invariant_candidate_ledger,
    save_elevation_review_ledger,
    save_invariant_candidate_ledger,
)
from constitutional.jpss.invariant_register import load_invariant_register
from constitutional.legitimacy.jpss_c_spec import (
    JPSS_C_ELEVATION_CRITERIA,
    JPSS_C_SELECTION_DIMENSIONS,
    SelectionOutcome,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

ELEVATION_THRESHOLD = 0.75
ESCALATION_THRESHOLD = 0.55


class InvariantSelectionRequest(BaseModel):
    candidate_value: str
    signal: str = ""
    purpose_clauses: list[str] = Field(default_factory=list)
    historical_failures: list[str] = Field(default_factory=list)
    identity_markers: list[str] = Field(default_factory=list)
    risk_models: list[str] = Field(default_factory=list)
    steward_proposals: list[str] = Field(default_factory=list)
    steward_id: str = "steward"
    protects_purpose: bool = False
    prevents_catastrophic_drift: bool = False
    defines_identity: bool = False
    constrains_unacceptable_actions: bool = False
    stabilizes_long_term_coherence: bool = False
    required_for_reconstructability: bool = False


class DimensionScore(BaseModel):
    dimension: str
    score: float = Field(ge=0.0, le=1.0)
    rationale: str = ""


class InvariantSelectionResult(BaseModel):
    candidate_value: str
    outcome: SelectionOutcome
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    composite_score: float = Field(default=0.0, ge=0.0, le=1.0)
    criteria_met: list[str] = Field(default_factory=list)
    criteria_failed: list[str] = Field(default_factory=list)
    rationale: str = ""
    captured_at: datetime | None = None


def _score_purpose_alignment(request: InvariantSelectionRequest, register_purpose: set[str]) -> DimensionScore:
    overlap = set(request.purpose_clauses) & register_purpose
    score = 1.0 if request.protects_purpose else (0.7 if overlap else 0.3)
    return DimensionScore(
        dimension="purpose_alignment",
        score=score,
        rationale="Aligns with registered purpose clauses." if overlap or request.protects_purpose else "Weak purpose alignment.",
    )


def _score_identity_protection(request: InvariantSelectionRequest, register_identity: set[str]) -> DimensionScore:
    overlap = set(request.identity_markers) & register_identity
    score = 1.0 if request.defines_identity else (0.6 if overlap else 0.2)
    return DimensionScore(
        dimension="identity_protection",
        score=score,
        rationale="Defines or reinforces identity markers." if score >= 0.6 else "Does not protect identity.",
    )


def _score_failure_prevention(request: InvariantSelectionRequest) -> DimensionScore:
    score = 0.9 if request.prevents_catastrophic_drift or request.historical_failures else 0.4
    return DimensionScore(
        dimension="failure_prevention",
        score=score,
        rationale="Addresses known historical failures." if request.historical_failures else "No failure history cited.",
    )


def _score_cross_era_stability(request: InvariantSelectionRequest) -> DimensionScore:
    score = 0.85 if request.stabilizes_long_term_coherence else 0.45
    return DimensionScore(
        dimension="cross_era_stability",
        score=score,
        rationale="Stabilizes long-term coherence." if request.stabilizes_long_term_coherence else "Uncertain cross-era stability.",
    )


def _score_reconstructability(request: InvariantSelectionRequest) -> DimensionScore:
    score = 1.0 if request.required_for_reconstructability else 0.35
    return DimensionScore(
        dimension="reconstructability",
        score=score,
        rationale="Required for reconstructability." if request.required_for_reconstructability else "Not reconstructability-critical.",
    )


def _score_sacred_constraint_fit(request: InvariantSelectionRequest, sacred: set[str]) -> DimensionScore:
    in_sacred = request.candidate_value.lower() in {s.lower() for s in sacred}
    score = 1.0 if request.constrains_unacceptable_actions or in_sacred else 0.4
    return DimensionScore(
        dimension="sacred_constraint_fit",
        score=score,
        rationale="Constrains unacceptable actions." if score >= 0.8 else "Not a sacred-constraint candidate.",
    )


def _score_misclassification_cost(request: InvariantSelectionRequest) -> DimensionScore:
    # Elevating spurious values is costly; adaptive default is safer when uncertain
    criteria_count = sum(
        1
        for flag in (
            request.protects_purpose,
            request.prevents_catastrophic_drift,
            request.defines_identity,
            request.constrains_unacceptable_actions,
            request.stabilizes_long_term_coherence,
            request.required_for_reconstructability,
        )
        if flag
    )
    score = min(1.0, criteria_count / 3)
    return DimensionScore(
        dimension="misclassification_cost",
        score=score,
        rationale=f"{criteria_count}/6 elevation criteria asserted.",
    )


def _evaluate_criteria(request: InvariantSelectionRequest) -> tuple[list[str], list[str]]:
    flags = {
        "protects_purpose": request.protects_purpose,
        "prevents_catastrophic_drift": request.prevents_catastrophic_drift,
        "defines_identity": request.defines_identity,
        "constrains_unacceptable_actions": request.constrains_unacceptable_actions,
        "stabilizes_long_term_coherence": request.stabilizes_long_term_coherence,
        "required_for_reconstructability": request.required_for_reconstructability,
    }
    met = [name for name in JPSS_C_ELEVATION_CRITERIA if flags.get(name, False)]
    failed = [name for name in JPSS_C_ELEVATION_CRITERIA if name not in met]
    return met, failed


def _resolve_outcome(composite: float, criteria_met: list[str]) -> SelectionOutcome:
    if composite >= ELEVATION_THRESHOLD and len(criteria_met) >= 3:
        return "elevate_to_invariant"
    if composite >= ESCALATION_THRESHOLD:
        return "escalate_to_constitutional_review"
    if composite < 0.35:
        return "reject"
    return "keep_adaptive"


class InvariantSelectionEngine:
    """Constitutional classifier — decides what becomes invariant."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def evaluate(self, request: InvariantSelectionRequest) -> InvariantSelectionResult:
        now = datetime.now(UTC).replace(microsecond=0)
        register = load_invariant_register(self.csr)
        latest = register.latest()

        purpose: set[str] = set()
        identity: set[str] = set()
        sacred: set[str] = set()
        if latest:
            purpose = set(latest.purpose_clauses)
            identity = set(latest.identity_markers)
            sacred = set(latest.sacred_constraints)

        dimension_scores = [
            _score_purpose_alignment(request, purpose),
            _score_identity_protection(request, identity),
            _score_failure_prevention(request),
            _score_cross_era_stability(request),
            _score_reconstructability(request),
            _score_sacred_constraint_fit(request, sacred),
            _score_misclassification_cost(request),
        ]
        assert len(dimension_scores) == len(JPSS_C_SELECTION_DIMENSIONS)

        composite = round(sum(d.score for d in dimension_scores) / len(dimension_scores), 4)
        criteria_met, criteria_failed = _evaluate_criteria(request)
        outcome = _resolve_outcome(composite, criteria_met)

        rationale_map = {
            "elevate_to_invariant": "Candidate satisfies constitutional elevation test.",
            "keep_adaptive": "Insufficient elevation criteria; remain adaptive.",
            "escalate_to_constitutional_review": "Borderline case requires constitutional review.",
            "reject": "Candidate fails constitutional elevation test.",
        }

        result = InvariantSelectionResult(
            candidate_value=request.candidate_value,
            outcome=outcome,
            dimension_scores=dimension_scores,
            composite_score=composite,
            criteria_met=criteria_met,
            criteria_failed=criteria_failed,
            rationale=rationale_map[outcome],
            captured_at=now,
        )

        candidate_ledger = load_invariant_candidate_ledger(self.csr)
        candidate_ledger.append(
            InvariantCandidateEntry(
                timestamp=now,
                steward_id=request.steward_id,
                candidate_value=request.candidate_value,
                signal=request.signal,
                purpose_clauses=list(request.purpose_clauses),
                historical_failures=list(request.historical_failures),
                identity_markers=list(request.identity_markers),
                steward_proposal="; ".join(request.steward_proposals) if request.steward_proposals else "",
            )
        )
        save_invariant_candidate_ledger(self.csr, candidate_ledger)

        elevation_ledger = load_elevation_review_ledger(self.csr)
        elevation_ledger.append(
            ElevationReviewEntry(
                timestamp=now,
                steward_id=request.steward_id,
                candidate_value=request.candidate_value,
                criteria_met=criteria_met,
                criteria_failed=criteria_failed,
                dimension_scores={d.dimension: d.score for d in dimension_scores},
                outcome=outcome,
                rationale=result.rationale,
                ratified=outcome == "elevate_to_invariant",
            )
        )
        save_elevation_review_ledger(self.csr, elevation_ledger)

        return result
