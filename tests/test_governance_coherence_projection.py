"""Tests for Alt-7.1 governance coherence projection."""

from __future__ import annotations

from src.jarvis_modular import (
    ModularContext,
    OperatorGovernanceCoherenceModule,
)
from src.operator_cognition_coherence_fabric import (
    build_governance_coherence_projection,
    format_governance_coherence_block,
    governance_coherence_projection_enabled,
)


def test_build_governance_coherence_projection_bounded():
    projection = build_governance_coherence_projection()
    assert projection["read_only"] is True
    assert projection["source"] == "operator_cognition_coherence_fabric"
    assert projection.get("authority_lane")
    assert "envelope_governance_modes" in projection
    assert len(projection.get("runtime_posture") or []) == 2


def test_format_governance_coherence_block_misaligned():
    block = format_governance_coherence_block(
        {"fabric_genes_aligned": False, "authority_lane": "operator"}
    )
    assert "misaligned" in block.lower()


def test_operator_governance_coherence_module_collect():
    module = OperatorGovernanceCoherenceModule()
    modules = module.collect(ModularContext(messages=[]))
    assert len(modules) == 1
    assert modules[0].channel == "governance"
    assert modules[0].metadata.get("read_only") is True
    assert "Governance coherence" in modules[0].content


def test_governance_projection_env_gate(monkeypatch):
    monkeypatch.setenv("AAIS_GOVERNANCE_COHERENCE_PROJECTION", "0")
    assert governance_coherence_projection_enabled() is False
    module = OperatorGovernanceCoherenceModule()
    assert module.collect(ModularContext(messages=[])) == []
