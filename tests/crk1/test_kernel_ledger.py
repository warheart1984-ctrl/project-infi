"""CRK-1 kernel ledger genesis entry tests."""

from __future__ import annotations

from src.crk1.kernel_ledger import (
    ASSIMILATION_LAYER,
    CONTINUITY_GUARANTEES,
    KERNEL_LEDGER_GENESIS_ENTRY_ID,
    PRESERVATION_LAYER,
    TRANSMISSION_LAYER,
    bootstrap_kernel_ledger_entry,
    create_genesis_kernel_ledger_entry,
)
from src.crk1.runtime_facade import CRK1Runtime


def test_genesis_kernel_ledger_entry_shape() -> None:
    entry = create_genesis_kernel_ledger_entry(
        timestamp="2026-03-22T00:00:00Z",
        root_signature="abc123",
    )
    assert entry.entry_id == KERNEL_LEDGER_GENESIS_ENTRY_ID
    assert entry.entry_type == "Constitutional Adoption Record"
    assert entry.parent is None
    assert entry.recorded_by == "Identity(Root)"
    assert entry.kernel_specification.transmission_layer == TRANSMISSION_LAYER
    assert entry.kernel_specification.preservation_layer == PRESERVATION_LAYER
    assert entry.kernel_specification.assimilation_layer == ASSIMILATION_LAYER
    assert entry.continuity_guarantees == CONTINUITY_GUARANTEES
    text = entry.to_canonical_text()
    assert "CRK‑1 Kernel Ledger Entry" in text
    assert "K0 — Consequence Transmission" in text
    assert "K12 — Semantic Exposure Metric" in text
    assert entry.signature == "abc123"
    assert len(entry.entry_hash()) == 64


def test_bootstrap_kernel_ledger_entry_on_runtime(crk1_runtime) -> None:
    facade = CRK1Runtime(crk1_runtime)
    entry = bootstrap_kernel_ledger_entry(facade)
    assert entry.replay_anchors.evidence_e0.admissible is True
    assert entry.replay_anchors.decision_d0.identity == "Root"
    assert entry.replay_anchors.outcome_o0.replayable is True
    assert entry.replay_anchors.evidence_e1.replay_of == entry.replay_anchors.outcome_o0.id
