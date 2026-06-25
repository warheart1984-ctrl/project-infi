"""Mission #006 — Calibration Assimilation (CAA-1 / CXD-1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.crk1.caa1_assimilation import (
    AssimilationContext,
    JudgmentQualitySample,
    build_caa1_receipt,
    compute_isolation_proof,
    validate_caa1,
)
from src.crk1.mission_006_calibration_assimilation import run_mission_006_calibration_assimilation
from src.crk1.schema_validator import CRK1SchemaValidator

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "crk1"


def test_caa1_schema_registered() -> None:
    CRK1SchemaValidator().validate(
        "CAA1ContinuityAssimilationReceipt",
        {
            "cxd_id": "cxd-test-001",
            "timestamp": "2026-06-22T20:00:00Z",
            "steward_id": "steward_s2",
            "isolation_proof": "a" * 64,
            "lineage_used": {"crr_hash": "b" * 64, "clg_hash": "c" * 64},
            "pre_assimilation_judgment": "d" * 64,
            "post_assimilation_judgment": "e" * 64,
            "assimilation_delta": 0.2,
            "assimilation_threshold": 0.15,
            "continuity_passed": True,
            "proof_bundle": "f" * 64,
        },
    )


def test_isolation_proof_rejects_participant() -> None:
    with pytest.raises(ValueError, match="isolation failed"):
        compute_isolation_proof("steward_a", ["steward_a", "steward_b"])


def test_build_caa1_receipt_continuity_pass() -> None:
    pre = JudgmentQualitySample("s2", "physics.fall", 0.7, False)
    post = JudgmentQualitySample("s2", "physics.fall", 0.0, True)
    receipt = build_caa1_receipt(
        AssimilationContext(
            steward_id="s2",
            original_participant_ids=["s1"],
            crr_hash="1" * 64,
            clg_hash="2" * 64,
            contradiction_class="physics.fall",
            pre_sample=pre,
            post_sample=post,
        )
    )
    validate_caa1(receipt)
    assert receipt["continuity_passed"] is True
    assert receipt["assimilation_delta"] >= receipt["assimilation_threshold"]


def test_mission_006_end_to_end() -> None:
    report = run_mission_006_calibration_assimilation()
    assert report.passed, report.failures
    assert report.continuity_passed
    assert report.caa1_receipt["cxd_id"]
    validate_caa1(report.caa1_receipt)


def test_sample_caa1_fixture_if_present() -> None:
    path = FIXTURES / "sample_caa1_receipt.json"
    if not path.exists():
        pytest.skip("sample fixture not generated")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    validate_caa1(receipt)
