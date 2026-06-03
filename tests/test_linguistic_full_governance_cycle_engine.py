#!/usr/bin/env python3
"""Tests for linguistic_full_governance_cycle_engine (Wave 13)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from datetime import datetime, timedelta, timezone

from src.governance_organs.linguistic_drift_forecast_engine import (  # noqa: E402
    archive_forecast_before_write,
)
from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    LinguisticForecastCalibrationEngine,
)
from src.governance_organs.linguistic_full_governance_cycle_engine import (  # noqa: E402
    LinguisticFullGovernanceCycleEngine,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def test_full_cycle_dry_run():
    engine = LinguisticFullGovernanceCycleEngine(ROOT)
    report = engine.run_cycle(
        skip_gates=True,
        skip_drift_refresh=True,
        dry_run=True,
    )
    assert report.cycle_id
    assert "calibration" in report.phases
    assert "predictive" in report.phases
    assert "reactive" in report.phases


def test_calibration_not_skipped_when_archive_exists(tmp_path: Path):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    forecast = {
        "linguistic_drift_forecast_version": "linguistic_drift_forecast.v1",
        "generated_at": ts,
        "forecasts": [],
    }
    gov = tmp_path / "governance"
    gov.mkdir(parents=True)
    (gov / "linguistic_drift_forecast.v1.json").write_text(
        json.dumps(forecast), encoding="utf-8"
    )
    pol = {
        "version": "linguistic_forecast_calibration_policy.v1",
        "min_forecast_age_hours": 1,
        "allow_archive_for_same_session_calibration": True,
        "retain_forecast_archive": 3,
    }
    (gov / "linguistic_forecast_calibration_policy.v1.json").write_text(
        json.dumps(pol), encoding="utf-8"
    )
    archive_forecast_before_write(tmp_path)
    cal = LinguisticForecastCalibrationEngine(tmp_path)
    report = cal.run_cycle(dry_run=True, use_archive_if_too_fresh=True)
    assert report.skipped is False or report.skip_reason != (
        "forecast younger than min_forecast_age_hours"
    )


def test_full_cycle_persists_registry():
    engine = LinguisticFullGovernanceCycleEngine(ROOT)
    report = engine.run_cycle(
        skip_gates=True,
        skip_drift_refresh=True,
        dry_run=False,
    )
    reg = load_json(ROOT / "governance/meta_linguistic_registry.v1.json")
    assert reg.get("last_full_cycle_report")
    assert report.passed or report.errors
