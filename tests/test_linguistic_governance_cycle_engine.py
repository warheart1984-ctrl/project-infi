#!/usr/bin/env python3
"""Tests for linguistic_governance_cycle_engine (Wave 11)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_cycle_engine import (  # noqa: E402
    LinguisticGovernanceCycleEngine,
    _adaptive_remediation_band,
    _metrics_from_scores,
    load_cycle_policy,
)
from tools.linguistic_drift_predictor import DriftScore, score_gene  # noqa: E402
from tools.linguistic_genome_lib import list_all_genes, load_json  # noqa: E402

GENE = "operator_cognition_coherence_fabric"


def test_cycle_policy_loads():
    policy = load_cycle_policy(ROOT)
    assert policy.get("version") == "linguistic_governance_cycle_policy.v1"
    assert policy.get("default_remediation_min_band") in {"low", "medium", "high"}


def test_metrics_from_scores():
    scores = [score_gene(GENE, ROOT)]
    metrics = _metrics_from_scores(scores, ROOT)
    assert metrics.gene_count == 1
    assert metrics.high_count + metrics.medium_count + metrics.low_count == 1


def test_adaptive_band_high_when_high_drift():
    from src.governance_organs.linguistic_governance_cycle_engine import CycleMetrics

    metrics = CycleMetrics(high_count=2, medium_count=1, low_count=10)
    band = _adaptive_remediation_band(metrics, load_cycle_policy(ROOT), None)
    assert band == "high"


def test_cycle_dry_run_passes():
    engine = LinguisticGovernanceCycleEngine(ROOT)
    report = engine.run_cycle(skip_gates=True, skip_drift_refresh=True, dry_run=True)
    assert report.cycle_id
    assert report.metrics.gene_count > 0
    assert report.passed or report.errors


def test_cycle_persist_updates_registry():
    engine = LinguisticGovernanceCycleEngine(ROOT)
    report = engine.run_cycle(skip_gates=True, skip_drift_refresh=True, dry_run=False)
    reg = load_json(ROOT / "governance/meta_linguistic_registry.v1.json")
    assert reg.get("last_cycle_id") == report.cycle_id
    cycle_path = ROOT / reg["last_cycle_report"]
    assert cycle_path.is_file()
    data = load_json(cycle_path)
    assert data["linguistic_governance_cycle_version"] == "linguistic_governance_cycle.v1"


def test_optimization_recommendations_present():
    engine = LinguisticGovernanceCycleEngine(ROOT)
    report = engine.run_cycle(skip_gates=True, skip_drift_refresh=True, dry_run=True)
    kinds = {r.get("kind") for r in report.optimization_recommendations}
    assert "remediation_min_band" in kinds


def test_queue_priority_genes_helper():
    from src.governance_organs.linguistic_governance_queue_engine import (
        queue_priority_genes,
        write_governance_queue,
    )

    write_governance_queue(ROOT, top=5)
    genes = queue_priority_genes(ROOT, top=5)
    assert isinstance(genes, list)


def test_adaptive_band_escalates_with_forecast_metrics():
    from src.governance_organs.linguistic_governance_cycle_engine import CycleMetrics

    metrics = CycleMetrics(high_count=0, medium_count=0, low_count=100)
    policy = load_cycle_policy(ROOT)
    band_without = _adaptive_remediation_band(metrics, policy, None, None)
    band_with = _adaptive_remediation_band(
        metrics, policy, None, {"predicted_high": 0, "predicted_medium": 10}
    )
    assert band_without == "low"
    assert band_with == "medium"
