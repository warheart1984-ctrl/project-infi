#!/usr/bin/env python3
"""Tests for linguistic_drift_forecast_engine (Wave 12)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_drift_forecast_engine import (  # noqa: E402
    build_preemptive_playbook,
    forecast_all,
    forecast_gene,
    forecast_metrics_from_report,
    write_forecast_report,
)
from tools.linguistic_drift_predictor import DriftScore, score_gene  # noqa: E402
from tools.linguistic_genome_lib import load_json  # noqa: E402

BAND_ORDER = {"high": 3, "medium": 2, "low": 1}

GENE = "capability_service_bridge"
PARENT = "operator_cognition_coherence_fabric"
EXPECTED_CHILDREN = {
    "ai_factory_organ",
    "continuity_witness_organ",
    "forge_contractor_organ",
    "jarvis_protocol_organ",
    "project_infi_state_machine_organ",
    "reasoning_executive_organ",
}


def test_latent_alignment_boosts_predicted_band():
    current = score_gene(GENE, ROOT)
    if current.signals.get("alignment_gap", 0) < 40:
        current = DriftScore(
            gene=GENE,
            drift_risk=current.drift_risk,
            band=current.band,
            signals={**current.signals, "alignment_gap": 45.0},
            recommendations=list(current.recommendations),
        )
    forecast = forecast_gene(GENE, ROOT, current=current, parents_at_risk=set())
    assert forecast.current_band == "low"
    assert BAND_ORDER.get(forecast.predicted_band, 0) >= BAND_ORDER["medium"]


def test_parent_forecast_boost_for_coherence_children():
    parents_at_risk = {PARENT}
    boosted = []
    for child in EXPECTED_CHILDREN:
        f = forecast_gene(child, ROOT, parents_at_risk=parents_at_risk)
        if f.signals.get("parent_forecast", 0) >= 10:
            boosted.append(child)
    assert len(boosted) >= 1


def test_forecast_report_writes_valid_json():
    path = write_forecast_report(ROOT)
    data = load_json(path)
    assert data["linguistic_drift_forecast_version"] == "linguistic_drift_forecast.v1"
    assert len(data.get("forecasts") or []) > 0
    metrics = forecast_metrics_from_report(data)
    assert "predicted_high" in metrics


def test_preemptive_playbook_has_watch_actions():
    forecasts = forecast_all(ROOT)
    medium_plus = [f for f in forecasts if f.predicted_band in {"medium", "high"}]
    if not medium_plus:
        f = forecasts[0]
    else:
        f = medium_plus[0]
    pb = build_preemptive_playbook(f, ROOT)
    assert pb["linguistic_preemptive_playbook_version"] == "linguistic_preemptive_playbook.v1"
    assert pb["gene"] == f.gene
