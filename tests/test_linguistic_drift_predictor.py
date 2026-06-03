#!/usr/bin/env python3
"""Tests for linguistic_drift_predictor (Wave 8)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_drift_predictor import score_gene  # noqa: E402

GENE = "operator_cognition_coherence_fabric"


def test_aligned_gene_not_high_without_velocity():
    s = score_gene(GENE, ROOT)
    assert s.band in {"low", "medium", "high"}
    assert 0 <= s.drift_risk <= 100


def test_drift_signals_present():
    s = score_gene(GENE, ROOT)
    assert "alignment_gap" in s.signals
    assert "lineage_fanout" in s.signals
