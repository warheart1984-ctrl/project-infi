#!/usr/bin/env python3
"""Tests for LinguisticGovernanceEngine (meta layer)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.governance_organs.linguistic_governance_engine import (  # noqa: E402
    GATE_COMMANDS,
    LinguisticGovernanceEngine,
)
from src.governance_organs import LinguisticGovernanceRuntime  # noqa: E402


def test_registry_loads():
    engine = LinguisticGovernanceEngine(ROOT)
    reg = engine.load_registry()
    assert reg.get("meta_linguistic_registry_version") == "meta_linguistic_registry.v1"
    assert "policy_mode" in reg
    assert reg.get("cascade_policy_ref")


def test_gate_commands_cover_registry_gates():
    engine = LinguisticGovernanceEngine(ROOT)
    reg = engine.load_registry()
    for gate in reg.get("gates") or []:
        assert gate in GATE_COMMANDS


def test_check_cascade_policy_returns_tuple():
    engine = LinguisticGovernanceEngine(ROOT)
    delta = {
        "gene": "operator_cognition_coherence_fabric",
        "before": {
            "mythic_label": "Coherence Fabric",
            "engineering_class": "OperatorCognitionCoherenceLayer",
        },
        "after": {
            "mythic_label": "Coherence Fabric",
            "engineering_class": "OperatorCognitionCoherenceLayer",
        },
    }
    errors, warnings = engine.check_cascade_policy(
        "operator_cognition_coherence_fabric", delta
    )
    assert isinstance(errors, list)
    assert isinstance(warnings, list)


def test_linguistic_governance_runtime_facade():
    assert LinguisticGovernanceRuntime.linguistic is LinguisticGovernanceEngine
