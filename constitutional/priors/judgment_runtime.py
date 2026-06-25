"""Prior Judgment Test — epistemic competence under prior shift (Article Q-7)."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.priors.reference_maps import (
    PRIOR_JUDGMENT_PASS_SCORE,
    ReferencePriorMap,
    StewardPriorAnswer,
    get_reference_prior_maps,
)
from constitutional.runtime.runtime import ConstitutionalStateRuntime

PRIOR_JUDGMENT_STATE_ID = "prior_judgment__latest"


class PriorJudgmentResult(BaseModel):
    passed: bool
    score: float
    missed_expected_signals: list[str] = Field(default_factory=list)
    false_expectations: list[str] = Field(default_factory=list)
    stability_inversions: list[str] = Field(default_factory=list)
    dismissed_fears: list[str] = Field(default_factory=list)
    evaluated_at: datetime | None = None


class PriorJudgmentState(BaseModel):
    state_id: str = PRIOR_JUDGMENT_STATE_ID
    state_type: str = "prior_judgment"
    version: int = Field(default=1, ge=1)
    steward_id: str = "steward"
    last_submitted_at: datetime | None = None
    steward_answers: dict[str, StewardPriorAnswer] = Field(default_factory=dict)
    last_result: PriorJudgmentResult | None = None
    passed: bool = False


class PriorJudgmentTest:
    """Evaluate steward prior answers against reference maps under prior shift."""

    def __init__(
        self,
        reference_prior_maps: dict[str, ReferencePriorMap] | None = None,
    ) -> None:
        self.reference_prior_maps = reference_prior_maps or get_reference_prior_maps()

    def evaluate(
        self,
        steward_prior_answers: dict[str, StewardPriorAnswer],
    ) -> PriorJudgmentResult:
        missed: list[str] = []
        false_hits: list[str] = []
        inversions: list[str] = []
        dismissed: list[str] = []

        scenario_ids = sorted(self.reference_prior_maps.keys())
        total = len(scenario_ids)
        correct = 0

        for scenario_id in scenario_ids:
            ref = self.reference_prior_maps[scenario_id]
            answer = steward_prior_answers.get(scenario_id)
            if answer is None:
                missed.append(scenario_id)
                continue

            expected_set = {signal.lower() for signal in answer.expected_signals}
            ref_expected = {signal.lower() for signal in ref.expected_signals}
            if ref_expected.issubset(expected_set):
                correct += 1
            else:
                missed.append(scenario_id)

            ref_false = {signal.lower() for signal in ref.false_expectations}
            if expected_set.intersection(ref_false):
                false_hits.append(scenario_id)

            ref_volatile = {item.lower() for item in ref.assumed_volatilities}
            for stability in answer.assumed_stabilities:
                if stability.lower() in ref_volatile:
                    inversions.append(scenario_id)

            ref_feared = {item.lower() for item in ref.feared_failures}
            answer_feared = {item.lower() for item in answer.feared_failures}
            if ref_feared and not ref_feared.intersection(answer_feared):
                dismissed.append(scenario_id)

        score = correct / total if total else 0.0
        passed = (
            score >= PRIOR_JUDGMENT_PASS_SCORE
            and not false_hits
            and not inversions
            and not dismissed
        )

        return PriorJudgmentResult(
            passed=passed,
            score=score,
            missed_expected_signals=missed,
            false_expectations=false_hits,
            stability_inversions=inversions,
            dismissed_fears=dismissed,
            evaluated_at=datetime.now(UTC).replace(microsecond=0),
        )


def load_prior_judgment_state(csr: ConstitutionalStateRuntime) -> PriorJudgmentState | None:
    try:
        doc = csr.get_domain_doc(PRIOR_JUDGMENT_STATE_ID, PriorJudgmentState)
        assert isinstance(doc, PriorJudgmentState)
        return doc
    except KeyError:
        return None


def submit_prior_judgment_answers(
    csr: ConstitutionalStateRuntime,
    answers: dict[str, StewardPriorAnswer],
    *,
    steward_id: str = "steward",
) -> PriorJudgmentState:
    now = datetime.now(UTC).replace(microsecond=0)
    prev = load_prior_judgment_state(csr)
    version = (prev.version + 1) if prev else 1

    merged: dict[str, StewardPriorAnswer] = {}
    if prev:
        merged.update(prev.steward_answers)
    merged.update(answers)

    result = PriorJudgmentTest().evaluate(merged)
    state = PriorJudgmentState(
        version=version,
        steward_id=steward_id,
        last_submitted_at=now,
        steward_answers=merged,
        last_result=result,
        passed=result.passed,
    )
    csr.register_or_replace_state(
        StateObject(
            state_id=PRIOR_JUDGMENT_STATE_ID,
            state_type="prior_judgment",
            current_state="Observed" if state.passed else "Proposed",
        )
    )
    csr.put_domain_doc(PRIOR_JUDGMENT_STATE_ID, "prior_judgment", state)
    return state


def seed_passing_prior_judgment(csr: ConstitutionalStateRuntime) -> PriorJudgmentState:
    """Canonical passing prior answers for tests and cold-start."""
    ref = get_reference_prior_maps()
    answers = {
        scenario_id: StewardPriorAnswer(
            scenario_id=scenario_id,
            expected_signals=list(ref_map.expected_signals),
            expected_risks=list(ref_map.expected_risks),
            assumed_stabilities=list(ref_map.assumed_stabilities),
            assumed_volatilities=list(ref_map.assumed_volatilities),
            feared_failures=list(ref_map.feared_failures),
            ignored_possibilities=list(ref_map.ignored_possibilities),
        )
        for scenario_id, ref_map in ref.items()
    }
    return submit_prior_judgment_answers(csr, answers)
