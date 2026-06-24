"""Integration tests — lawful LLM adapter + CRR-1 + CLG-1."""

from __future__ import annotations

from src.crk1.crr1_validator import validate_crr1
from src.crk1.lawful_llm_adapter import FallingObjectModel, LawfulLLMAdapter
from src.crk1.mission_005_calibration_lineage_stress import (
    run_mission_005_calibration_lineage_stress,
)


class DummyModel:
    def __call__(self, prompt: str) -> dict[str, object]:
        return {"outcome": 0.9, "confidence": 0.8, "assumptions": ["linear"]}


def test_lawful_llm_end_to_end() -> None:
    llm = LawfulLLMAdapter(DummyModel())

    exp = llm.predict("What will happen?")
    assert exp.expected_confidence == 0.8

    evidence = llm.observe({"value": 0.2, "strength": 1.0})

    correction, crr1 = llm.correct(exp, evidence)

    assert correction.model_shift.magnitude > 0
    assert crr1["contradiction_delta"] > 0
    assert validate_crr1(crr1)

    assert crr1["expected_outcome"] == exp.expected_outcome
    assert crr1["observed_outcome"] == evidence.observed_outcome


def test_lawful_llm_ask_emits_governance_header() -> None:
    llm = LawfulLLMAdapter(DummyModel(), steward_id="steward_llm")
    raw, grr = llm.ask("decide")
    assert raw["outcome"] == 0.9
    assert grr.action_type == "llm_decision"
    assert grr.invariants_checked["K0_K2"] == "PASS"


def test_falling_object_mvcd() -> None:
    llm = LawfulLLMAdapter(FallingObjectModel(), channel_id="physics.fall")
    correction, crr1 = llm.run_falling_object_scenario()

    assert correction.model_shift.magnitude == 0.7
    assert crr1["expected_outcome"] == 1.0
    assert crr1["observed_outcome"] == 0.3
    assert crr1["calibration_delta"] != 0
    assert validate_crr1(crr1)


def test_mission_005_calibration_lineage_stress() -> None:
    report = run_mission_005_calibration_lineage_stress()
    assert report.passed, report.failures
    assert report.crr_count == 3
    assert report.calibration_event_count == 3
    assert len(report.lineage) == 3
