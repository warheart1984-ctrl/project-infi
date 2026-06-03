#!/usr/bin/env python3
"""Smoke tests for linguistic_lineage_viz (Wave 7)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.linguistic_lineage_viz import build_mermaid, load_genomes  # noqa: E402

GENE = "operator_cognition_coherence_fabric"


def test_ego_graph_contains_known_parent_edge():
    genes = load_genomes(ROOT)
    include = {GENE}
    for parent in (genes[GENE].get("lineage") or {}).get("parents") or []:
        include.add(parent)
    mermaid = build_mermaid(genes, include=include)
    assert "operator_profile_organ" in mermaid or "adaptive_lane_organ" in mermaid
    assert GENE in mermaid
    assert "-->" in mermaid
