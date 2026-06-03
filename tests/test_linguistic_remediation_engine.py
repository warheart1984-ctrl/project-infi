#!/usr/bin/env python3
"""Tests for linguistic_remediation_engine (Wave 9)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_remediation_engine import build_playbook  # noqa: E402
from tools.linguistic_drift_predictor import DriftScore, score_gene  # noqa: E402

GENE = "operator_cognition_coherence_fabric"


def test_high_drift_playbook_has_actions():
    score = DriftScore(
        gene=GENE,
        drift_risk=80,
        band="high",
        signals={"alignment_gap": 50, "lineage_fanout": 6},
        recommendations=["review engineering_class alignment"],
    )
    playbook = build_playbook(score, ROOT)
    assert playbook["drift_band"] == "high"
    kinds = {a.get("kind") for a in playbook.get("actions") or []}
    assert kinds, "high drift should produce at least one action"
    assert "translator_rerun" in kinds or "mp_ling_draft" in kinds or "wave2_header" in kinds


def test_low_drift_playbook_minimal_actions():
    score = DriftScore(
        gene="nonexistent_gene_xyz",
        drift_risk=5,
        band="low",
        signals={},
        recommendations=[],
    )
    playbook = build_playbook(score, ROOT)
    assert playbook["drift_band"] == "low"
    assert playbook.get("actions") == []


def test_live_gene_playbook_builds():
    score = score_gene(GENE, ROOT)
    playbook = build_playbook(score, ROOT)
    assert playbook["gene"] == GENE
    assert playbook["drift_band"] == score.band
