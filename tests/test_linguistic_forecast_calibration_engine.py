#!/usr/bin/env python3
"""Tests for linguistic_forecast_calibration_engine (Wave 13)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    _classify_outcome_v2,
    calibrate_forecast,
    load_calibration_policy,
    write_calibration_report,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def test_classify_false_alarm():
    assert _classify_outcome_v2("medium", "low") == "false_alarm"


def test_classify_miss():
    assert _classify_outcome_v2("low", "medium") == "miss"


def test_classify_stable():
    assert _classify_outcome_v2("low", "low") == "stable"


def test_calibrate_with_fixture_forecast():
    forecast_path = ROOT / "governance/linguistic_drift_forecast.v1.json"
    if not forecast_path.is_file():
        return
    forecast = load_json(forecast_path)
    report = calibrate_forecast(ROOT, forecast=forecast)
    if report is None:
        return
    assert report["linguistic_forecast_calibration_version"] == "linguistic_forecast_calibration.v1"
    assert len(report.get("gene_records") or []) > 0
    outcomes = {r["band_outcome"] for r in report["gene_records"]}
    assert outcomes & {"stable", "false_alarm", "miss", "hit"}


def test_calibration_policy_loads():
    policy = load_calibration_policy(ROOT)
    assert policy.get("version") == "linguistic_forecast_calibration_policy.v1"
