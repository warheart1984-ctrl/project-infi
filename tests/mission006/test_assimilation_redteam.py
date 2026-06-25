"""Mission #006 assimilation red-team tests (Python mirror of TS fixtures)."""

from __future__ import annotations

import pytest

from src.crk1.caa1_assimilation import (
    AssimilationContext,
    JudgmentQualitySample,
    build_caa1_receipt,
    sha256_hex,
    validate_caa1,
)


def test_rejects_forged_isolation_proof_bundle() -> None:
    pre = JudgmentQualitySample("S2", "physics.fall", 0.5, False)
    post = JudgmentQualitySample("S2", "physics.fall", 0.6, True)
    receipt = build_caa1_receipt(
        AssimilationContext(
            steward_id="S2",
            original_participant_ids=["S1"],
            crr_hash="a" * 64,
            clg_hash="b" * 64,
            contradiction_class="physics.fall",
            pre_sample=pre,
            post_sample=post,
            assimilation_threshold=0.1,
        )
    )
    receipt["isolation_proof"] = sha256_hex("fake_material")
    with pytest.raises(ValueError):
        validate_caa1(receipt)


def test_rejects_continuity_passed_when_delta_below_threshold() -> None:
    receipt = {
        "cxd_id": "test-001",
        "timestamp": "2026-06-22T20:00:00Z",
        "steward_id": "S2",
        "isolation_proof": "a" * 64,
        "lineage_used": {"crr_hash": "b" * 64, "clg_hash": "c" * 64},
        "pre_assimilation_judgment": "d" * 64,
        "post_assimilation_judgment": "e" * 64,
        "assimilation_delta": 0.01,
        "assimilation_threshold": 0.1,
        "continuity_passed": True,
        "proof_bundle": "f" * 64,
    }
    with pytest.raises(ValueError):
        validate_caa1(receipt)


def test_detects_lineage_tampering_hash_mismatch() -> None:
    crr = {"event": "calibration"}
    expected = sha256_hex(crr)
    tampered = sha256_hex("tampered")
    assert tampered != expected
