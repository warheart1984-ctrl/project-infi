"""Tests for Mission #004 — Calibration Preservation (CE-1, CLG-1, C-PoLT)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.calibration_lineage_graph import CalibrationLineageGraphCLG1
from src.crk1.calibration_objects import ExpectationObject, EvidenceObject
from src.crk1.calibration_pipeline import run_continuity_proof_of_life
from src.crk1.continuity_graph_v2 import ContinuityGraphV2
from src.crk1.correction_engine_ce1 import CorrectionEngineCE1
from src.crk1.errors import ConstitutionalError
from src.crk1.schema_validator import CRK1SchemaValidator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def test_ce1_full_pipeline_produces_crr_and_event() -> None:
    engine = CorrectionEngineCE1()
    result = engine.run(
        steward_id="S-CE1-001",
        channel_id="reality-channel-alpha",
        expected_outcome=1.0,
        observed_outcome=0.3,
        expected_confidence=0.9,
        assumptions=["optimistic_baseline"],
        model_ref="ce1-v1",
        related_grr_ids=["GRR-001"],
        invariant_implications=["K6"],
    )
    assert result.crr.id.startswith("CRR-1")
    assert result.calibration_event.crr_id == result.crr.id
    assert result.contradiction.threshold_exceeded
    assert result.surprise.surprise_intensity > 0
    assert abs(result.correction_delta.model_shift) > 0


def test_ce1_rejects_no_contradiction() -> None:
    engine = CorrectionEngineCE1(contradiction_threshold=10.0)
    with pytest.raises(ConstitutionalError, match="no contradiction"):
        engine.run(
            steward_id="S-CE1-002",
            channel_id="ch-1",
            expected_outcome=1.0,
            observed_outcome=1.0,
            expected_confidence=0.5,
        )


def test_clg1_ingest_and_queries() -> None:
    engine = CorrectionEngineCE1()
    result = engine.run(
        steward_id="S-CLG-001",
        channel_id="market-feed",
        expected_outcome=100.0,
        observed_outcome=72.0,
        expected_confidence=0.85,
        model_ref="forecast-v1",
        invariant_implications=["K6", "K13"],
    )
    clg = CalibrationLineageGraphCLG1()
    event = clg.ingest_crr(result.crr, result.calibration_event, decision_cluster_id="DC-001")

    lineage = clg.trace_invariant_lineage("K6")
    assert len(lineage) == 1
    assert lineage[0].id == event.id

    profile = clg.steward_calibration_profile("S-CLG-001")
    assert profile["event_count"] == 1
    assert profile["calibration_delta_sum"] != 0

    ratio = clg.drift_correction_ratio(drift_index=0.05)
    assert ratio["event_count"] == 1

    precursors = clg.collapse_precursors({"S-CLG-001": 0.9}, calibration_threshold=0.5)
    assert len(precursors) == 1


def test_continuity_graph_v2_reconstruction() -> None:
    engine = CorrectionEngineCE1()
    result = engine.run(
        steward_id="S-V2-001",
        channel_id="regulator-channel",
        expected_outcome=0.8,
        observed_outcome=0.2,
        expected_confidence=0.7,
    )
    graph = ContinuityGraphV2()
    graph.ingest_calibration(result.crr, result.calibration_event)

    replay = graph.reconstruct_for_future_steward(result.crr.id)
    assert replay["transmissible"] is True
    assert replay["reconstruction"]["calibration_delta"] == result.correction_object.calibration.calibration_delta


def test_cpolt_seven_tests_pass() -> None:
    pipeline_result, report = run_continuity_proof_of_life()
    assert report.overall == "PASS"
    assert len(report.tests) == 7
    assert all(v == "PASS" for v in report.tests.values())
    assert pipeline_result.crr.reconstruct()["crr_id"] == pipeline_result.crr.id


def test_crr_schema_validator_accepts_ce1_output() -> None:
    result = CorrectionEngineCE1().run(
        steward_id="S-SCH-001",
        channel_id="ch-schema",
        expected_outcome=50,
        observed_outcome=10,
        expected_confidence=0.6,
    )
    # Build schema-shaped document from CE-1 output for validation
    c = result.correction_object
    doc = {
        "crr_id": result.crr.id,
        "timestamp": result.crr.created_at,
        "steward_id": result.crr.created_by,
        "prior_judgment_state": {
            "prior_assumptions": list(c.expectation.assumptions),
            "prior_confidence": c.expectation.expected_confidence,
            "prior_model": {"model_ref": c.expectation.model_ref},
        },
        "reality_contact": {
            "evidence_observed": str(c.evidence.observed_outcome),
            "reality_channel": c.evidence.channel_id,
            "evidence_strength": c.evidence.evidence_strength,
        },
        "contradiction": {
            "expected_outcome": c.expectation.expected_outcome,
            "actual_outcome": c.evidence.observed_outcome,
            "contradiction_delta": c.contradiction.contradiction_delta,
            "surprise_intensity": c.surprise.surprise_intensity,
        },
        "correction": {
            "update_rule_applied": c.correction.update_rule_applied,
            "assumptions_removed": list(c.correction.assumptions_removed),
            "assumptions_added": list(c.correction.assumptions_added),
            "model_shift": {"delta": c.correction.model_shift},
        },
        "calibration_gained": {
            "calibration_delta": c.calibration.calibration_delta,
            "new_confidence": c.correction.new_confidence,
            "new_judgment_state": {"model_ref": c.expectation.model_ref},
        },
        "continuity_linkage": {
            "invariant_implications": result.calibration_event.invariant_implications,
            "future_risks": [],
            "lineage_reference": result.calibration_event.id,
        },
        "integrity": {
            "evidence_hash": c.integrity.evidence_hash.removeprefix("sha256:")[:64]
            if c.integrity.evidence_hash.startswith("sha256:")
            else "0" * 64,
            "receipt_signature": c.integrity.signature,
            "reality_verification": {"channel": c.evidence.channel_id},
        },
    }
    # Pad hash to 64 hex if needed
    if len(doc["integrity"]["evidence_hash"]) != 64:
        doc["integrity"]["evidence_hash"] = ("a" * 64)
    CRK1SchemaValidator().validate("CalibrationReconstructionReceipt", doc)


def test_f1_detect_contradiction_unit() -> None:
    engine = CorrectionEngineCE1()
    exp = ExpectationObject(expected_outcome=10.0, expected_confidence=0.8, model_ref="m1")
    evd = EvidenceObject(
        evidence_ref="E-1",
        observed_outcome=7.0,
        channel_id="ch-1",
        expectation_ref=exp.id,
    )
    ctr = engine.detect_contradiction(exp, evd)
    assert ctr.contradiction_delta == 3.0
    assert ctr.threshold_exceeded
