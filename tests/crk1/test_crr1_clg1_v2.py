"""Tests for CRR-1 builder, CLG-1 ingestion, and Continuity Graph v2."""

from __future__ import annotations

from src.crk1.calibration_objects import (
    ContradictionObject,
    CorrectionDeltaObject,
    EvidenceObject,
    ExpectationObject,
    SurpriseObject,
)
from src.crk1.calibration_pipeline import CalibrationResult
from src.crk1.clg1_ingestion import CLG1Ingestion
from src.crk1.clg1_store import InMemoryCLG1Store
from src.crk1.continuity_graph_v2 import ContinuityGraphV2
from src.crk1.crr1_builder import build_crr1
from src.crk1.crr1_validator import validate_crr1
from src.crk1.lawful_llm_adapter import LawfulLLMAdapter


def _sample_calibration_result() -> CalibrationResult:
    expectation = ExpectationObject(
        expected_outcome=1.0,
        expected_confidence=0.9,
        assumptions=["vacuum"],
        model_ref="test",
        decision_ref="D-001",
    )
    evidence = EvidenceObject(
        evidence_ref="E-physics",
        observed_outcome=0.3,
        channel_id="physics.fall",
        expectation_ref=expectation.id,
    )
    contradiction = ContradictionObject(
        expectation_ref=expectation.id,
        evidence_ref=evidence.id,
        contradiction_delta=0.7,
        threshold_exceeded=True,
    )
    surprise = SurpriseObject(
        contradiction_ref=contradiction.id,
        expectation_ref=expectation.id,
        surprise_intensity=0.63,
        prior_confidence=0.9,
    )
    correction = CorrectionDeltaObject(
        surprise_ref=surprise.id,
        update_rule_applied="bayesian_update",
        model_shift=-0.7,
        new_confidence=0.83,
    )
    return CalibrationResult(
        expectation=expectation,
        evidence=evidence,
        contradiction=contradiction,
        surprise=surprise,
        correction=correction,
        calibration_delta=-0.7,
        future_implications=["recalibrate fall model"],
        steward_id="steward_llm",
        decision_id="D-001",
    )


def test_build_crr1_from_calibration_result() -> None:
    result = _sample_calibration_result()
    crr1 = build_crr1(result)

    assert crr1["receipt_type"] == "CRR-1"
    assert crr1["contradiction_delta"] == 0.7
    assert crr1["calibration_change"] == -0.7
    assert crr1["links"]["decision_id"] == "D-001"
    assert validate_crr1(crr1)


def test_clg1_ingestion_creates_event_and_edges() -> None:
    store = InMemoryCLG1Store()
    ingestion = CLG1Ingestion(store)
    crr1 = build_crr1(_sample_calibration_result())

    event_id = ingestion.ingest_crr1(crr1)
    assert event_id in store.nodes
    assert any(edge.kind == "PERFORMED_CALIBRATION" for edge in store.edges)
    assert any(edge.kind == "CORRECTS_DECISION" for edge in store.edges)


def test_continuity_graph_v2_record_and_query() -> None:
    graph = ContinuityGraphV2()
    crr1 = build_crr1(_sample_calibration_result())
    event_id = graph.record_calibration_event(crr1)

    lineage = graph.get_steward_lineage("steward_llm")
    assert len(lineage) == 1
    assert lineage[0]["crr_id"] == crr1["crr_id"]

    corrections = graph.get_decision_corrections("D-001")
    assert len(corrections) == 1
    assert graph.store_event_index[crr1["crr_id"]] == event_id


def test_lawful_llm_records_into_continuity_graph_v2() -> None:
    class _Model:
        def __call__(self, prompt: str) -> dict[str, object]:
            return {"outcome": 0.9, "confidence": 0.8, "assumptions": ["linear"]}

    graph = ContinuityGraphV2()
    llm = LawfulLLMAdapter(_Model(), steward_id="steward_llm", continuity_graph=graph)
    exp = llm.predict("What will happen?")
    evidence = llm.observe({"value": 0.2, "strength": 1.0})
    _correction, crr1 = llm.correct(exp, evidence)

    assert validate_crr1(crr1)
    assert len(graph.get_steward_lineage("steward_llm")) == 1
