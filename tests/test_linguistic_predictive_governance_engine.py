#!/usr/bin/env python3
"""Tests for linguistic_predictive_governance_engine (Wave 12)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_predictive_governance_engine import (  # noqa: E402
    LinguisticPredictiveGovernanceEngine,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def test_predictive_cycle_dry_run():
    engine = LinguisticPredictiveGovernanceEngine(ROOT)
    report = engine.run_cycle(skip_drift_refresh=True, dry_run=True)
    assert report.cycle_id
    assert report.metrics.gene_count > 0
    assert report.passed or report.errors


def test_predictive_cycle_updates_registry():
    engine = LinguisticPredictiveGovernanceEngine(ROOT)
    report = engine.run_cycle(skip_drift_refresh=True, dry_run=False)
    reg = load_json(ROOT / "governance/meta_linguistic_registry.v1.json")
    assert reg.get("last_forecast_report")
    assert reg.get("last_predictive_cycle_at") == report.generated_at
    forecast_path = ROOT / reg["last_forecast_report"]
    assert forecast_path.is_file()
