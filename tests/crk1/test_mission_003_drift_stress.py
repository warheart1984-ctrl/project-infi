"""Mission #003 — Drift Envelope Stress Tests (M3-C)."""

from __future__ import annotations

from src.crk1.drift_stress_protocol import DriftStressProtocol
from src.crk1.external_reproduction_harness import prepare_continuity_substrate
from src.crk1.reproduction_certifier import Mission003Certifier


def test_drift_stress_battery(runtime) -> None:
    prepare_continuity_substrate(runtime)
    report = DriftStressProtocol(runtime).run_all()
    assert report.passed, report.summary()
    assert len(report.by_category("C1")) == 3
    assert len(report.by_category("C2")) == 2
    assert len(report.by_category("C3")) == 4


def test_mission_003_certification(runtime) -> None:
    report = Mission003Certifier(runtime).certify()
    assert report.certified, report.to_json()
    assert report.levels.r3_reproduction
    assert report.levels.r4_red_team
    assert report.levels.r5_drift
    assert report.drift_tests_passed == report.drift_tests_run
    assert report.packet_fingerprint
