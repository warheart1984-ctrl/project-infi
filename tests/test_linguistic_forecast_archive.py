#!/usr/bin/env python3
"""Tests for Wave 14 forecast archive + archive-aware calibration."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_drift_forecast_engine import (  # noqa: E402
    archive_forecast_before_write,
    load_latest_forecast_archive,
)
from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    load_prior_forecast_for_calibration,
)


def _seed_forecast(root: Path, *, hours_ago: float = 0) -> None:
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    payload = {
        "linguistic_drift_forecast_version": "linguistic_drift_forecast.v1",
        "generated_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "forecasts": [{"gene": "test_gene", "predicted_band": "medium", "current_band": "low"}],
    }
    out = root / "governance/linguistic_drift_forecast.v1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload), encoding="utf-8")
    policy = {
        "version": "linguistic_forecast_calibration_policy.v1",
        "min_forecast_age_hours": 1,
        "retain_forecast_archive": 3,
        "allow_archive_for_same_session_calibration": True,
    }
    pol_path = root / "governance/linguistic_forecast_calibration_policy.v1.json"
    pol_path.write_text(json.dumps(policy), encoding="utf-8")


def test_archive_before_write(tmp_path: Path):
    _seed_forecast(tmp_path, hours_ago=2)
    dest = archive_forecast_before_write(tmp_path)
    assert dest is not None
    assert dest.parent.name == "linguistic_forecast_archive"
    archived = load_latest_forecast_archive(tmp_path)
    assert archived is not None
    assert archived["forecasts"][0]["gene"] == "test_gene"


def test_calibration_uses_archive_when_live_too_fresh(tmp_path: Path):
    _seed_forecast(tmp_path, hours_ago=0)
    archive_forecast_before_write(tmp_path)
    forecast, _, source = load_prior_forecast_for_calibration(
        tmp_path, use_archive_if_too_fresh=True
    )
    assert forecast is not None
    assert source == "archive"


def test_calibration_uses_live_when_old_enough(tmp_path: Path):
    _seed_forecast(tmp_path, hours_ago=2)
    forecast, _, source = load_prior_forecast_for_calibration(tmp_path)
    assert forecast is not None
    assert source == "live"
