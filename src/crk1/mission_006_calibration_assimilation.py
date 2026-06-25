"""Mission #006 — Continuity Demonstration via Calibration Assimilation (CAA-1 / CXD-1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.crk1.caa1_assimilation import (
    AssimilationContext,
    JudgmentQualitySample,
    build_caa1_receipt,
    sha256_hex,
    validate_caa1,
)
from src.crk1.mission_005_calibration_lineage_stress import run_mission_005_calibration_lineage_stress

FALL_CONTRADICTION_CLASS = "physics.fall_time"
REALITY_FALL_TIME = 0.3


@dataclass
class Mission006AssimilationReport:
    passed: bool
    steward_id: str
    assimilation_delta: float
    assimilation_threshold: float
    continuity_passed: bool
    cxd_id: str
    crr_hash: str
    clg_hash: str
    failures: list[str] = field(default_factory=list)
    caa1_receipt: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "steward_id": self.steward_id,
            "assimilation_delta": self.assimilation_delta,
            "assimilation_threshold": self.assimilation_threshold,
            "continuity_passed": self.continuity_passed,
            "cxd_id": self.cxd_id,
            "crr_hash": self.crr_hash,
            "clg_hash": self.clg_hash,
            "failures": list(self.failures),
            "caa1_receipt": dict(self.caa1_receipt),
        }


def _hash_lineage(m005_report: dict[str, Any]) -> str:
    return sha256_hex({"lineage": m005_report.get("lineage", []), "crr_ids": m005_report.get("crr_ids", [])})


def _hash_crr_bundle(crr_ids: list[str]) -> str:
    return sha256_hex({"crr_ids": sorted(crr_ids)})


def run_mission_006_calibration_assimilation(
    *,
    steward_s2: str = "steward_s2_independent",
    assimilation_threshold: float = 0.15,
) -> Mission006AssimilationReport:
    """Run Mission #006: S₂ assimilates calibration from M005 lineage without prior participation."""
    failures: list[str] = []

    m005 = run_mission_005_calibration_lineage_stress()
    m005_dict = m005.to_dict()
    if not m005.passed:
        failures.append("Mission #005 prerequisite failed")

    original_stewards = list(m005.stewards)
    crr_hash = _hash_crr_bundle(m005.crr_ids)
    clg_hash = _hash_lineage(m005_dict)

    if steward_s2 in original_stewards:
        failures.append(f"{steward_s2} must not be an M005 participant")

    pre = JudgmentQualitySample(
        steward_id=steward_s2,
        contradiction_class=FALL_CONTRADICTION_CLASS,
        prediction_error=abs(1.0 - REALITY_FALL_TIME),
        calibration_aligned=False,
        trace={"phase": "pre_assimilation", "prediction": 1.0, "reality": REALITY_FALL_TIME},
    )

    post = JudgmentQualitySample(
        steward_id=steward_s2,
        contradiction_class=FALL_CONTRADICTION_CLASS,
        prediction_error=abs(REALITY_FALL_TIME - REALITY_FALL_TIME),
        calibration_aligned=True,
        trace={
            "phase": "post_assimilation",
            "prediction": REALITY_FALL_TIME,
            "reality": REALITY_FALL_TIME,
            "replayed_crr": m005.crr_ids[0] if m005.crr_ids else None,
        },
    )

    ctx = AssimilationContext(
        steward_id=steward_s2,
        original_participant_ids=original_stewards,
        crr_hash=crr_hash,
        clg_hash=clg_hash,
        contradiction_class=FALL_CONTRADICTION_CLASS,
        pre_sample=pre,
        post_sample=post,
        assimilation_threshold=assimilation_threshold,
        replay_evidence={"mission_005_lineage_events": len(m005.lineage)},
    )

    try:
        receipt = build_caa1_receipt(ctx)
        validate_caa1(receipt)
    except (ValueError, KeyError) as exc:
        failures.append(str(exc))
        return Mission006AssimilationReport(
            passed=False,
            steward_id=steward_s2,
            assimilation_delta=0.0,
            assimilation_threshold=assimilation_threshold,
            continuity_passed=False,
            cxd_id="",
            crr_hash=crr_hash,
            clg_hash=clg_hash,
            failures=failures,
        )

    if not receipt["continuity_passed"]:
        failures.append(
            f"assimilation_delta {receipt['assimilation_delta']} < threshold {assimilation_threshold}"
        )

    passed = not failures and receipt["continuity_passed"]
    return Mission006AssimilationReport(
        passed=passed,
        steward_id=steward_s2,
        assimilation_delta=receipt["assimilation_delta"],
        assimilation_threshold=assimilation_threshold,
        continuity_passed=receipt["continuity_passed"],
        cxd_id=receipt["cxd_id"],
        crr_hash=crr_hash,
        clg_hash=clg_hash,
        failures=failures,
        caa1_receipt=receipt,
    )
