"""Tests for CRK-1 Mutation Ledger."""

from __future__ import annotations

from src.crk1.drift_simulator import DriftSimulator
from src.crk1.mutation_ledger import CRK1MutationLedger


def test_mutation_ledger_records_drift_test(runtime, semantic_monitor) -> None:
    runtime.create_evidence()
    ledger = CRK1MutationLedger()
    simulator = DriftSimulator(runtime, semantic_monitor=semantic_monitor, mutation_ledger=ledger)
    mutation = {"target": "interpretation", "changes": {}}
    result = simulator.test_drift_with_exposure(mutation)

    assert len(ledger.entries) == 1
    entry = ledger.entries[0]
    assert entry.exposure_before.se >= 0
    assert entry.exposure_after.se >= entry.exposure_before.se - 1e-9
    assert result["constitutional"] is True

    text = ledger.to_canonical_text()
    assert "CRK‑1 Mutation Ledger" in text
    assert "K11: Interpretive Drift Envelope" in text
    assert entry.signature
