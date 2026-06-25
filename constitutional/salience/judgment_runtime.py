"""Salience Judgment Test — perceptual competence under novelty (Article Q-6)."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.core.models import StateObject
from constitutional.runtime.runtime import ConstitutionalStateRuntime
from constitutional.salience.reference_maps import (
    SALIENCE_JUDGMENT_PASS_SCORE,
    ReferenceSalienceMap,
    StewardSalienceAnswer,
    get_reference_salience_maps,
)

SALIENCE_JUDGMENT_STATE_ID = "salience_judgment__latest"


class SalienceJudgmentResult(BaseModel):
    passed: bool
    score: float
    salience_misreads: list[str] = Field(default_factory=list)
    missed_primary_signals: list[str] = Field(default_factory=list)
    false_signals: list[str] = Field(default_factory=list)
    risk_misprioritization: list[str] = Field(default_factory=list)
    evaluated_at: datetime | None = None


class SalienceJudgmentState(BaseModel):
    state_id: str = SALIENCE_JUDGMENT_STATE_ID
    state_type: str = "salience_judgment"
    version: int = Field(default=1, ge=1)
    steward_id: str = "steward"
    last_submitted_at: datetime | None = None
    steward_answers: dict[str, StewardSalienceAnswer] = Field(default_factory=dict)
    last_result: SalienceJudgmentResult | None = None
    passed: bool = False


class SalienceJudgmentTest:
    """Evaluate steward salience answers against reference perceptual maps."""

    def __init__(
        self,
        reference_salience_maps: dict[str, ReferenceSalienceMap] | None = None,
    ) -> None:
        self.reference_salience_maps = reference_salience_maps or get_reference_salience_maps()

    def evaluate(
        self,
        steward_salience_answers: dict[str, StewardSalienceAnswer],
    ) -> SalienceJudgmentResult:
        misreads: list[str] = []
        missed: list[str] = []
        false_hits: list[str] = []
        risk_mis: list[str] = []

        scenario_ids = sorted(self.reference_salience_maps.keys())
        total = len(scenario_ids)
        correct = 0

        for scenario_id in scenario_ids:
            ref = self.reference_salience_maps[scenario_id]
            answer = steward_salience_answers.get(scenario_id)
            if answer is None:
                missed.append(scenario_id)
                continue

            primary_set = {signal.lower() for signal in answer.primary_signals}
            ref_primary = {signal.lower() for signal in ref.primary_signals}
            if ref_primary.issubset(primary_set):
                correct += 1
            else:
                missed.append(scenario_id)

            ref_false = {signal.lower() for signal in ref.false_signals}
            if primary_set.intersection(ref_false):
                false_hits.append(scenario_id)

            if [signal.lower() for signal in answer.risk_order] != [
                signal.lower() for signal in ref.risk_order
            ]:
                risk_mis.append(scenario_id)

        score = correct / total if total else 0.0
        passed = (
            score >= SALIENCE_JUDGMENT_PASS_SCORE
            and not false_hits
            and not risk_mis
        )

        return SalienceJudgmentResult(
            passed=passed,
            score=score,
            salience_misreads=misreads,
            missed_primary_signals=missed,
            false_signals=false_hits,
            risk_misprioritization=risk_mis,
            evaluated_at=datetime.now(UTC).replace(microsecond=0),
        )


def load_salience_judgment_state(csr: ConstitutionalStateRuntime) -> SalienceJudgmentState | None:
    try:
        doc = csr.get_domain_doc(SALIENCE_JUDGMENT_STATE_ID, SalienceJudgmentState)
        assert isinstance(doc, SalienceJudgmentState)
        return doc
    except KeyError:
        return None


def submit_salience_judgment_answers(
    csr: ConstitutionalStateRuntime,
    answers: dict[str, StewardSalienceAnswer],
    *,
    steward_id: str = "steward",
) -> SalienceJudgmentState:
    now = datetime.now(UTC).replace(microsecond=0)
    prev = load_salience_judgment_state(csr)
    version = (prev.version + 1) if prev else 1

    merged: dict[str, StewardSalienceAnswer] = {}
    if prev:
        merged.update(prev.steward_answers)
    merged.update(answers)

    result = SalienceJudgmentTest().evaluate(merged)
    state = SalienceJudgmentState(
        version=version,
        steward_id=steward_id,
        last_submitted_at=now,
        steward_answers=merged,
        last_result=result,
        passed=result.passed,
    )
    csr.register_or_replace_state(
        StateObject(
            state_id=SALIENCE_JUDGMENT_STATE_ID,
            state_type="salience_judgment",
            current_state="Observed" if state.passed else "Proposed",
        )
    )
    csr.put_domain_doc(SALIENCE_JUDGMENT_STATE_ID, "salience_judgment", state)
    return state


def seed_passing_salience_judgment(csr: ConstitutionalStateRuntime) -> SalienceJudgmentState:
    """Canonical passing salience answers for tests and cold-start."""
    ref = get_reference_salience_maps()
    answers = {
        scenario_id: StewardSalienceAnswer(
            scenario_id=scenario_id,
            primary_signals=list(ref_map.primary_signals),
            secondary_signals=list(ref_map.secondary_signals),
            ignored_signals=list(ref_map.ignored_signals),
            risk_order=list(ref_map.risk_order),
        )
        for scenario_id, ref_map in ref.items()
    }
    return submit_salience_judgment_answers(csr, answers)
