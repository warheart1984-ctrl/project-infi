"""JPSS-C Constitutional Judgment Exam — classify adaptive vs invariant boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.legitimacy.jpss_c_spec import ConstitutionalClassification
from constitutional.runtime.runtime import ConstitutionalStateRuntime

JPSS_C_EXAM_STATE_ID = "jpss_c_exam__latest"


class ConstitutionalScenarioType(str, Enum):
    ADAPTIVE = "adaptive_domain"
    INVARIANT = "invariant_domain"
    BOUNDARY = "boundary_consultation"
    LEGITIMACY = "requires_legitimacy_review"


class ConstitutionalScenario(BaseModel):
    scenario_id: str
    scenario_type: ConstitutionalScenarioType
    description: str
    canonical_classification: ConstitutionalClassification


class ConstitutionalResponse(BaseModel):
    scenario_id: str
    classification: ConstitutionalClassification


class ConstitutionalScenarioResult(BaseModel):
    scenario_id: str
    expected: ConstitutionalClassification
    actual: ConstitutionalClassification
    passed: bool


class JPSSCExamResult(BaseModel):
    steward_id: str
    evaluated_at: datetime
    scenarios_total: int
    scenarios_passed: int
    passed: bool
    results: list[ConstitutionalScenarioResult] = Field(default_factory=list)


CANONICAL_CONSTITUTIONAL_SCENARIOS: tuple[ConstitutionalScenario, ...] = (
    ConstitutionalScenario(
        scenario_id="C1",
        scenario_type=ConstitutionalScenarioType.ADAPTIVE,
        description="Update calibration threshold after repeated outcome failure.",
        canonical_classification="adaptive_domain",
    ),
    ConstitutionalScenario(
        scenario_id="C2",
        scenario_type=ConstitutionalScenarioType.INVARIANT,
        description="Remove sacred constraint blocking succession gate.",
        canonical_classification="invariant_domain",
    ),
    ConstitutionalScenario(
        scenario_id="C3",
        scenario_type=ConstitutionalScenarioType.BOUNDARY,
        description="Rephrase purpose clause for clarity without intent change.",
        canonical_classification="boundary_consultation",
    ),
    ConstitutionalScenario(
        scenario_id="C4",
        scenario_type=ConstitutionalScenarioType.LEGITIMACY,
        description="Alter core value ranking under operational pressure.",
        canonical_classification="requires_legitimacy_review",
    ),
)


class JPSSCExam:
    """Evaluate constitutional judgment — how invariant classifications are made."""

    def __init__(
        self,
        scenarios: tuple[ConstitutionalScenario, ...] = CANONICAL_CONSTITUTIONAL_SCENARIOS,
    ) -> None:
        self.scenarios = scenarios

    def evaluate(
        self,
        steward_id: str,
        responses: list[ConstitutionalResponse],
    ) -> JPSSCExamResult:
        now = datetime.now(UTC).replace(microsecond=0)
        results: list[ConstitutionalScenarioResult] = []
        passed_count = 0

        for scenario in self.scenarios:
            response = next((r for r in responses if r.scenario_id == scenario.scenario_id), None)
            if response is None:
                results.append(
                    ConstitutionalScenarioResult(
                        scenario_id=scenario.scenario_id,
                        expected=scenario.canonical_classification,
                        actual="adaptive_domain",
                        passed=False,
                    )
                )
                continue
            ok = response.classification == scenario.canonical_classification
            if ok:
                passed_count += 1
            results.append(
                ConstitutionalScenarioResult(
                    scenario_id=scenario.scenario_id,
                    expected=scenario.canonical_classification,
                    actual=response.classification,
                    passed=ok,
                )
            )

        return JPSSCExamResult(
            steward_id=steward_id,
            evaluated_at=now,
            scenarios_total=len(self.scenarios),
            scenarios_passed=passed_count,
            passed=passed_count == len(self.scenarios),
            results=results,
        )


def run_jpss_c_exam(
    csr: ConstitutionalStateRuntime,
    steward_id: str,
    responses: list[ConstitutionalResponse],
) -> JPSSCExamResult:
    result = JPSSCExam().evaluate(steward_id, responses)
    csr.put_domain_doc(JPSS_C_EXAM_STATE_ID, "jpss_c_exam_result", result)
    return result


def load_jpss_c_exam_result(csr: ConstitutionalStateRuntime) -> JPSSCExamResult | None:
    try:
        doc = csr.get_domain_doc(JPSS_C_EXAM_STATE_ID, JPSSCExamResult)
        assert isinstance(doc, JPSSCExamResult)
        return doc
    except KeyError:
        return None


def canonical_passing_constitutional_responses() -> list[ConstitutionalResponse]:
    return [
        ConstitutionalResponse(scenario_id=s.scenario_id, classification=s.canonical_classification)
        for s in CANONICAL_CONSTITUTIONAL_SCENARIOS
    ]
