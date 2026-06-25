"""Stewardship Balancing Test — meta-judgment competence evaluation."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.runtime.runtime import ConstitutionalStateRuntime

STEWARDSHIP_BALANCING_STATE_ID = "stewardship_balancing__latest"


class StewardshipClassification(str, Enum):
    MUST_CHANGE = "Must Change"
    MUST_NOT_CHANGE = "Must Not Change"
    CONDITIONAL_CHANGE = "Conditional Change"
    REQUIRES_REFLECTION = "Requires Reflection"
    REQUIRES_INVARIANT_CONSULTATION = "Requires Invariant Consultation"


StewardshipScenarioType = Literal["adaptive", "invariant", "ambiguous"]

_AMBIGUOUS_ALLOWED: frozenset[StewardshipClassification] = frozenset(
    {
        StewardshipClassification.CONDITIONAL_CHANGE,
        StewardshipClassification.REQUIRES_REFLECTION,
        StewardshipClassification.REQUIRES_INVARIANT_CONSULTATION,
    }
)


class StewardshipScenario(BaseModel):
    scenario_id: str
    scenario_type: StewardshipScenarioType
    description: str
    canonical_classification: StewardshipClassification


class StewardshipResponse(BaseModel):
    scenario_id: str
    classification: StewardshipClassification


class StewardshipScenarioResult(BaseModel):
    scenario_id: str
    scenario_type: StewardshipScenarioType
    expected: StewardshipClassification
    actual: StewardshipClassification
    passed: bool
    reason: str = ""


class StewardshipBalancingResult(BaseModel):
    steward_id: str
    evaluated_at: datetime
    scenarios_total: int
    scenarios_passed: int
    passed: bool
    adaptive_competence: bool
    invariant_competence: bool
    balancing_competence: bool
    results: list[StewardshipScenarioResult] = Field(default_factory=list)
    over_adaptation_risk: bool = False
    over_rigidity_risk: bool = False


CANONICAL_STEWARDSHIP_SCENARIOS: tuple[StewardshipScenario, ...] = (
    StewardshipScenario(
        scenario_id="A1",
        scenario_type="adaptive",
        description="Environment shifted; calibration thresholds are outdated for current risk profile.",
        canonical_classification=StewardshipClassification.MUST_CHANGE,
    ),
    StewardshipScenario(
        scenario_id="A2",
        scenario_type="adaptive",
        description="Outcome register shows repeated failure; reflection should update calibration.",
        canonical_classification=StewardshipClassification.MUST_CHANGE,
    ),
    StewardshipScenario(
        scenario_id="I1",
        scenario_type="invariant",
        description="Proposal to remove sacred constraint: bypass succession gate for speed.",
        canonical_classification=StewardshipClassification.MUST_NOT_CHANGE,
    ),
    StewardshipScenario(
        scenario_id="I2",
        scenario_type="invariant",
        description="Proposal to reinterpret core value 'non-derogable' as optional under pressure.",
        canonical_classification=StewardshipClassification.MUST_NOT_CHANGE,
    ),
    StewardshipScenario(
        scenario_id="B1",
        scenario_type="ambiguous",
        description="Update salience weights for a newly discovered signal class.",
        canonical_classification=StewardshipClassification.CONDITIONAL_CHANGE,
    ),
    StewardshipScenario(
        scenario_id="B2",
        scenario_type="ambiguous",
        description="Amend purpose clause wording for clarity without changing intent.",
        canonical_classification=StewardshipClassification.REQUIRES_INVARIANT_CONSULTATION,
    ),
)


def _evaluate_response(
    scenario: StewardshipScenario,
    response: StewardshipResponse,
) -> StewardshipScenarioResult:
    actual = response.classification
    expected = scenario.canonical_classification

    if scenario.scenario_type == "adaptive":
        passed = actual == StewardshipClassification.MUST_CHANGE
        reason = "" if passed else f"Adaptive scenario requires {expected.value}."
    elif scenario.scenario_type == "invariant":
        passed = actual == StewardshipClassification.MUST_NOT_CHANGE
        reason = "" if passed else f"Invariant scenario requires {expected.value}."
    else:
        passed = actual in _AMBIGUOUS_ALLOWED
        reason = "" if passed else "Ambiguous scenario requires balanced classification."

    return StewardshipScenarioResult(
        scenario_id=scenario.scenario_id,
        scenario_type=scenario.scenario_type,
        expected=expected,
        actual=actual,
        passed=passed,
        reason=reason,
    )


class StewardshipBalancingTest:
    """Evaluate whether a steward can distinguish what must change vs what must not."""

    def __init__(
        self,
        csr: ConstitutionalStateRuntime,
        *,
        scenarios: tuple[StewardshipScenario, ...] = CANONICAL_STEWARDSHIP_SCENARIOS,
    ) -> None:
        self.csr = csr
        self.scenarios = scenarios
        self._by_id = {scenario.scenario_id: scenario for scenario in scenarios}

    def evaluate(
        self,
        steward_id: str,
        responses: list[StewardshipResponse],
    ) -> StewardshipBalancingResult:
        now = datetime.now(UTC).replace(microsecond=0)
        results: list[StewardshipScenarioResult] = []

        for scenario in self.scenarios:
            response = next((r for r in responses if r.scenario_id == scenario.scenario_id), None)
            if response is None:
                results.append(
                    StewardshipScenarioResult(
                        scenario_id=scenario.scenario_id,
                        scenario_type=scenario.scenario_type,
                        expected=scenario.canonical_classification,
                        actual=StewardshipClassification.REQUIRES_REFLECTION,
                        passed=False,
                        reason="No response provided.",
                    )
                )
                continue
            results.append(_evaluate_response(scenario, response))

        adaptive_results = [r for r in results if r.scenario_type == "adaptive"]
        invariant_results = [r for r in results if r.scenario_type == "invariant"]
        ambiguous_results = [r for r in results if r.scenario_type == "ambiguous"]

        adaptive_competence = all(r.passed for r in adaptive_results)
        invariant_competence = all(r.passed for r in invariant_results)
        balancing_competence = all(r.passed for r in ambiguous_results)

        over_adaptation = any(
            r.scenario_type == "invariant" and r.actual == StewardshipClassification.MUST_CHANGE
            for r in results
        )
        over_rigidity = any(
            r.scenario_type == "adaptive" and r.actual == StewardshipClassification.MUST_NOT_CHANGE
            for r in results
        )

        passed = (
            adaptive_competence
            and invariant_competence
            and balancing_competence
            and not over_adaptation
            and not over_rigidity
        )

        return StewardshipBalancingResult(
            steward_id=steward_id,
            evaluated_at=now,
            scenarios_total=len(self.scenarios),
            scenarios_passed=sum(1 for r in results if r.passed),
            passed=passed,
            adaptive_competence=adaptive_competence,
            invariant_competence=invariant_competence,
            balancing_competence=balancing_competence,
            results=results,
            over_adaptation_risk=over_adaptation,
            over_rigidity_risk=over_rigidity,
        )


def run_stewardship_balancing_test(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
    responses: list[StewardshipResponse],
) -> StewardshipBalancingResult:
    result = StewardshipBalancingTest(csr).evaluate(steward_id, responses)
    csr.put_domain_doc(STEWARDSHIP_BALANCING_STATE_ID, "stewardship_balancing_result", result)
    return result


def load_stewardship_balancing_result(csr: ConstitutionalStateRuntime) -> StewardshipBalancingResult | None:
    try:
        doc = csr.get_domain_doc(STEWARDSHIP_BALANCING_STATE_ID, StewardshipBalancingResult)
        assert isinstance(doc, StewardshipBalancingResult)
        return doc
    except KeyError:
        return None


def canonical_passing_responses() -> list[StewardshipResponse]:
    """Reference responses that satisfy all stewardship balancing criteria."""
    return [
        StewardshipResponse(scenario_id=s.scenario_id, classification=s.canonical_classification)
        for s in CANONICAL_STEWARDSHIP_SCENARIOS
    ]
