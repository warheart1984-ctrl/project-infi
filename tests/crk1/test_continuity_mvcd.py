"""Tests for Continuity Codex stack — MVCD, C-PoLT, SCT, RAI, CFE, calibration pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.calibration_pipeline import run_continuity_proof_of_life
from src.crk1.continuity_failure_equation import CFEInputs, evaluate_continuity_failure
from src.crk1.errors import ConstitutionalError
from src.crk1.governance_receipt_header import assess_invariants_checked
from src.crk1.reality_access_index import compute_reality_access_index, rai_drift_negative
from src.crk1.reality_contact_layer import ControlLevel, RealityDomain, RealitySurfaceRegistry
from src.crk1.schema_validator import CRK1SchemaValidator
from src.crk1.stewardship_calibration_test import SCTInputs, run_stewardship_calibration_test

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def test_mvcd_cpolt_all_pass() -> None:
    result, report = run_continuity_proof_of_life()
    assert report.overall == "PASS"
    assert result.sct_report["result"] == "PASS"
    assert result.cfe_report["continuity_intact"] is True
    assert result.crr.id.startswith("CRR-1")
    CRK1SchemaValidator().validate("CorrectionObject", result.correction.to_dict())
    CRK1SchemaValidator().validate("CalibrationCorrectionReceipt", result.crr.to_dict())


def test_cpolt_reconstruction_replays_calibration() -> None:
    result, _ = run_continuity_proof_of_life()
    replay = result.crr.reconstruct()
    assert replay["contradiction"]["threshold_exceeded"] is True
    assert replay["surprise"]["surprise_intensity"] > 0
    assert replay["calibration_delta"] != 0


def test_sct_fails_without_correction() -> None:
    report = run_stewardship_calibration_test(
        SCTInputs(
            evidence=0.2,
            calibration_prior=1.0,
            calibration_post=1.0,
            contradiction_magnitude=0.8,
            surprise_response=0.0,
        )
    )
    assert report.result == "FAIL"


def test_cfe_detects_no_correction() -> None:
    report = evaluate_continuity_failure(
        CFEInputs(
            ce=1.0,
            contradiction_magnitude=0.5,
            surprise_response=0.3,
            calibration_delta=0.0,
        )
    )
    assert report.cfe_triggered is True
    assert "no_correction" in report.failure_modes


def test_rai_composite() -> None:
    registry = RealitySurfaceRegistry(min_uncontrolled_domains=2)
    registry.add(
        RealityDomain(
            domain_id="D_ext",
            label="external",
            control_level=ControlLevel.NONE,
            consequence_intensity=0.9,
        )
    )
    rai = compute_reality_access_index(rdi=0.8, ce=0.9, se=0.85, registry=registry)
    assert 0.0 < rai <= 1.0
    assert rai_drift_negative([0.9, 0.85, 0.8, 0.75])


def test_governance_header_v12_invariants() -> None:
    checked = assess_invariants_checked({"transition_ok": True, "rcl_ok": True, "komega_ok": True})
    assert checked["K13_K15"] == "PASS"
    assert checked["KΩ"] == "PASS"


def test_pipeline_rejects_no_contradiction() -> None:
    from src.crk1.calibration_pipeline import run_calibration_pipeline

    with pytest.raises(ConstitutionalError, match="no contradiction"):
        run_calibration_pipeline(
            steward_id="S-1",
            channel_id="ch-1",
            expected_outcome=1.0,
            observed_outcome=1.0,
            expected_confidence=0.9,
        )
