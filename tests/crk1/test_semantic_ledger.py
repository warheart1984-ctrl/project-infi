"""Tests for CRK-1 Semantic Ledger."""

from __future__ import annotations

from src.crk1.semantic_ledger import CRK1SemanticLedger, bootstrap_semantic_ledger


def test_semantic_ledger_sync_and_canonical_text(runtime) -> None:
    evidence = runtime.create_evidence()
    frame = runtime.get_dominant_interpretation()
    runtime.generate_prediction(frame.id, evidence.id)
    runtime.get_reconstructions_for_evidence(evidence.id)

    ledger = bootstrap_semantic_ledger(runtime)
    text = ledger.to_canonical_text()

    assert "CRK‑1 Semantic Ledger" in text
    assert "InterpretationObject" in text
    assert "PredictionObject" in text
    assert "ReconstructionObject" in text
    assert "K7: Interpretive Pluralism" in text
    assert ledger.signature
    assert len(ledger.entries) >= 3


def test_semantic_ledger_append_only(runtime) -> None:
    ledger = CRK1SemanticLedger()
    added = ledger.sync_from_runtime(runtime)
    assert added >= 2
    before = len(ledger.entries)
    ledger.sync_from_runtime(runtime)
    assert len(ledger.entries) > before
