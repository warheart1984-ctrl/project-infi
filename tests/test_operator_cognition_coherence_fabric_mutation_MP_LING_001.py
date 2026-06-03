#!/usr/bin/env python3
"""Tests for MP-LING-001 linguistic_layer mutation (Wave 5)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_mutation_engine import (  # noqa: E402
    apply_linguistic_mutation,
    rollback_linguistic_mutation,
    validate_linguistic_delta,
)
from src.governance_organs.mutation_engine import MutationEngine  # noqa: E402
from tools.linguistic_genome_lib import load_aliases, load_genome, load_json  # noqa: E402

GENE = "operator_cognition_coherence_fabric"
MP_ID = "MP-LING-001"


def test_mp_ling_001_delta_validates():
    root = ROOT
    genome = load_genome(GENE, root)
    assert genome is not None
    delta = load_json(
        root / "schemas/deltas/operator_cognition_coherence_fabric_MP-LING-001_linguistic.json"
    )
    failures = validate_linguistic_delta(delta, genome, load_aliases(root))
    assert failures == []


def test_mp_ling_001_verify():
    engine = MutationEngine(ROOT)
    result = engine.verify(GENE, MP_ID)
    assert result.passed, result.failures


def test_mp_ling_001_dry_run():
    ok, failures = apply_linguistic_mutation(MP_ID, GENE, ROOT, dry_run=True)
    assert ok, failures


def test_mp_ling_001_apply_and_rollback():
    before = load_genome(GENE, ROOT)
    assert before is not None
    before_mythic = (before.get("ssp") or {}).get("mythic_label")
    ok, failures = apply_linguistic_mutation(MP_ID, GENE, ROOT)
    assert ok, failures
    after = load_genome(GENE, ROOT)
    assert after is not None
    assert (after.get("ssp") or {}).get("mythic_label") == "Coherence Fabric (cross-plane)"
    assert (after.get("ssp") or {}).get("linguistic_version") == "1.0.1"
    assert rollback_linguistic_mutation(MP_ID, GENE, ROOT)
    restored = load_genome(GENE, ROOT)
    assert restored is not None
    assert (restored.get("ssp") or {}).get("mythic_label") == before_mythic
