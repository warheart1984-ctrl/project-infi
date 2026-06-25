"""Significance Judgment Test v1 — constitutional competence evaluator."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.significance.reference_lattice import (
    SIGNIFICANCE_JUDGMENT_PASS_SCORE,
    SYNTHETIC_ARTIFACTS,
    ReferenceRationale,
    get_reference_lattice,
    get_reference_rationales,
)

SIGNIFICANCE_JUDGMENT_STATE_ID = "significance_judgment__latest"
MIN_RATIONALE_LENGTH = 20


class StewardSignificanceAnswer(BaseModel):
    artifact_id: str
    tier: int = Field(ge=0, le=4)
    rationale: str
    invariant_links: list[str] = Field(default_factory=list)
    purpose_links: list[str] = Field(default_factory=list)
    evidence_that_would_change: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    answered_at: datetime | None = None
    steward_id: str = "steward"


class SignificanceJudgmentResult(BaseModel):
    passed: bool
    score: float
    failures: list[str] = Field(default_factory=list)
    rationale_gaps: list[str] = Field(default_factory=list)
    invariant_mislinks: list[str] = Field(default_factory=list)
    consequence_blindspots: list[str] = Field(default_factory=list)
    evaluated_at: datetime | None = None


class SignificanceJudgmentState(BaseModel):
    state_id: str = SIGNIFICANCE_JUDGMENT_STATE_ID
    state_type: str = "significance_judgment"
    version: int = Field(default=1, ge=1)
    steward_id: str = "steward"
    last_submitted_at: datetime | None = None
    steward_answers: dict[str, StewardSignificanceAnswer] = Field(default_factory=dict)
    last_result: SignificanceJudgmentResult | None = None
    passed: bool = False


class SignificanceJudgmentRuntime:
    """Evaluates steward answers against the canonical reference lattice."""

    def __init__(
        self,
        reference_lattice: dict[str, int] | None = None,
        reference_rationales: dict[str, ReferenceRationale] | None = None,
    ) -> None:
        self.reference_lattice = reference_lattice or get_reference_lattice()
        self.reference_rationales = reference_rationales or get_reference_rationales()

    def evaluate(
        self,
        steward_answers: dict[str, StewardSignificanceAnswer],
    ) -> SignificanceJudgmentResult:
        failures: list[str] = []
        rationale_gaps: list[str] = []
        invariant_mislinks: list[str] = []
        consequence_blindspots: list[str] = []

        artifact_ids = sorted(self.reference_lattice.keys())
        total = len(artifact_ids)
        correct = 0

        for artifact_id in artifact_ids:
            ref_tier = self.reference_lattice[artifact_id]
            ref_rat = self.reference_rationales[artifact_id]
            answer = steward_answers.get(artifact_id)

            if answer is None:
                failures.append(artifact_id)
                rationale_gaps.append(artifact_id)
                invariant_mislinks.append(artifact_id)
                consequence_blindspots.append(artifact_id)
                continue

            if self._tier_aligned(answer, ref_tier, ref_rat):
                correct += 1
            else:
                failures.append(artifact_id)

            if not self._rationale_matches(answer.rationale, ref_rat):
                rationale_gaps.append(artifact_id)

            if not self._invariants_linked(answer, ref_rat):
                invariant_mislinks.append(artifact_id)

            if not answer.consequences:
                consequence_blindspots.append(artifact_id)

        score = correct / total if total else 0.0
        passed = (
            score >= SIGNIFICANCE_JUDGMENT_PASS_SCORE
            and not rationale_gaps
            and not invariant_mislinks
        )

        return SignificanceJudgmentResult(
            passed=passed,
            score=score,
            failures=failures,
            rationale_gaps=rationale_gaps,
            invariant_mislinks=invariant_mislinks,
            consequence_blindspots=consequence_blindspots,
            evaluated_at=datetime.now(UTC).replace(microsecond=0),
        )

    def _tier_aligned(
        self,
        answer: StewardSignificanceAnswer,
        ref_tier: int,
        ref_rat: ReferenceRationale,
    ) -> bool:
        if ref_rat.acceptable_tiers:
            return answer.tier in ref_rat.acceptable_tiers
        return answer.tier == ref_tier

    def _rationale_matches(self, steward_rat: str, ref_rat: ReferenceRationale) -> bool:
        if not steward_rat or len(steward_rat.strip()) < MIN_RATIONALE_LENGTH:
            return False
        lowered = steward_rat.lower()
        return any(keyword in lowered for keyword in ref_rat.keywords)

    def _invariants_linked(
        self,
        answer: StewardSignificanceAnswer,
        ref_rat: ReferenceRationale,
    ) -> bool:
        if not answer.invariant_links:
            return False
        if not ref_rat.required_invariant_themes:
            return True
        joined = " ".join(link.lower() for link in answer.invariant_links)
        return any(theme in joined for theme in ref_rat.required_invariant_themes)


def load_significance_judgment_state(
    csr: ConstitutionalStateRuntime,
) -> SignificanceJudgmentState | None:
    try:
        doc = csr.get_domain_doc(SIGNIFICANCE_JUDGMENT_STATE_ID, SignificanceJudgmentState)
        assert isinstance(doc, SignificanceJudgmentState)
        return doc
    except KeyError:
        return None


def submit_significance_judgment_answers(
    csr: ConstitutionalStateRuntime,
    answers: dict[str, StewardSignificanceAnswer],
    *,
    steward_id: str = "steward",
    submitted_at: datetime | None = None,
) -> SignificanceJudgmentState:
    """Record steward significance judgments and evaluate against the reference lattice."""
    now = submitted_at or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)

    prev = load_significance_judgment_state(csr)
    version = (prev.version + 1) if prev else 1

    merged: dict[str, StewardSignificanceAnswer] = {}
    if prev:
        merged.update(prev.steward_answers)

    for artifact_id, answer in answers.items():
        if artifact_id not in SYNTHETIC_ARTIFACTS:
            continue
        merged[artifact_id] = answer.model_copy(
            update={
                "artifact_id": artifact_id,
                "answered_at": now,
                "steward_id": steward_id,
            }
        )

    runtime = SignificanceJudgmentRuntime()
    result = runtime.evaluate(merged)

    state = SignificanceJudgmentState(
        version=version,
        steward_id=steward_id,
        last_submitted_at=now,
        steward_answers=merged,
        last_result=result,
        passed=result.passed,
    )
    csr.register_or_replace_state(
        StateObject(
            state_id=SIGNIFICANCE_JUDGMENT_STATE_ID,
            state_type="significance_judgment",
            current_state="Observed" if state.passed else "Proposed",
        )
    )
    csr.put_domain_doc(SIGNIFICANCE_JUDGMENT_STATE_ID, "significance_judgment", state)
    return state


def seed_passing_significance_judgment(
    csr: ConstitutionalStateRuntime,
    *,
    steward_id: str = "steward",
) -> SignificanceJudgmentState:
    """Submit canonical passing answers for all synthetic artifacts (tests / cold-start)."""
    answers = {
        "artifact_a": StewardSignificanceAnswer(
            artifact_id="artifact_a",
            tier=0,
            rationale=(
                "Emergency steward bypass concentrates hidden authority and violates Tier 0 "
                "anti-corruption and anti-capture invariants; it threatens Purpose Continuity "
                "by creating an unaudited escape hatch from runtime checks."
            ),
            invariant_links=["ANTI_CORRUPTION", "ANTI_CAPTURE", "PURPOSE_CONTINUITY"],
            purpose_links=["Purpose Continuity"],
            evidence_that_would_change=[
                "Time-bound dual-control emergency scope with automatic sunset and public receipt"
            ],
            consequences=[
                "Misclassification enables constitutional capture and undetected authority erosion"
            ],
        ),
        "artifact_b": StewardSignificanceAnswer(
            artifact_id="artifact_b",
            tier=2,
            rationale=(
                "Seasonal environmental context is a contextual frame (Tier 2) that shapes "
                "interpretation of invariants without altering sacred core doctrine; it must "
                "be preserved for continuity."
            ),
            invariant_links=["CONTEXTUAL_INTERPRETATION", "CONTINUITY"],
            purpose_links=["interpretation continuity"],
            evidence_that_would_change=[
                "Ledger entries that directly override Tier 0 prohibitions would reclassify upward"
            ],
            consequences=[
                "Treating context as doctrine causes cargo-cult constitutional drift"
            ],
        ),
        "artifact_c": StewardSignificanceAnswer(
            artifact_id="artifact_c",
            tier=3,
            rationale=(
                "An organic cultural ritual among early stewards is a historical artifact "
                "(Tier 3) unless it encodes a core structural invariant; it is not incidental "
                "implementation detail."
            ),
            invariant_links=["HISTORICAL_STEWARD_CULTURE", "CULTURAL_CONTINUITY"],
            purpose_links=["steward lineage context"],
            evidence_that_would_change=[
                "Evidence the ritual encodes a non-derogable structural invariant would elevate to Tier 1"
            ],
            consequences=[
                "Confusing culture with constitution produces false Tier 0 claims and blocks legitimate evolution"
            ],
        ),
    }
    return submit_significance_judgment_answers(csr, answers, steward_id=steward_id)


def check_succession_readiness(
    csr: ConstitutionalStateRuntime,
    steward_answers: dict[str, StewardSignificanceAnswer] | None = None,
) -> tuple[bool, str]:
    """Significance Judgment gate for succession readiness."""
    if steward_answers is not None:
        result = SignificanceJudgmentRuntime().evaluate(steward_answers)
    else:
        state = load_significance_judgment_state(csr)
        if state is None or state.last_result is None:
            return False, "Succession blocked: steward has not completed Significance Judgment Test"
        result = state.last_result

    if not result.passed:
        return (
            False,
            f"Succession blocked: steward failed Significance Judgment Test. Score={result.score}",
        )
    return True, "Succession readiness satisfied."
